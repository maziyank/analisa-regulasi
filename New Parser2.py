#!/usr/bin/env python
# coding: utf-8

# In[866]:


import fitz
import pdfquery
import regex as re
from slugify import slugify
import dominate
from dominate.tags import *
import markdown
import os


# In[867]:


PASAL_PATTERN = r"^Pasal\s+\d+"
BAB_PATTERN = r"^BAB\s+[A-Z]+"
BAGIAN_PATTERN = r"^Bagian\s+Ke[a-z]+"
PARAGRAPH_PATTERN = r"^Paragraf\s+\d+"

def save_cp(text, path, fn):
    if os.path.isfile(path):
        path = path.split("/")[-1]
        path = re.sub(r"\.[a-z0-9]+$", "", path)
    if not os.path.exists(path):
        os.mkdir(path);
    with open(f"{path}/{fn}",'w', encoding='utf-8') as f:
        f.write(text)

def exctract_reg_text(filename):
    def line_to_skip(text):
        text = re.sub(r'\s+(\.\s+){3}', '...', text)
        text = re.sub(r'\s+…', '...', text)
        text = re.sub(r'\s+\.\.\.[^[\.]]', '...', text)

        skip_patterns = [
            "^SK\s+No\s+\d+.+?A$",
            "^\w\.{3}$",
            "^www.+\.go\.id%",
            "^\-\s{0,3}\d+\s{0,3}\-",
            "^(\d{4},\s+No.\s*\d+)",
            "^(\d{4},\s*No.\s*\d+\s*-\s{0,3}\d+\s{0,3}\-)"
        ]

        for pattern in skip_patterns:
            if re.match(pattern, text):
                return True

        return False

    def extract_pages(doc):
        line_text = []
        for index, page in enumerate(doc):
            data = page.get_text("dict")
            for block in data['blocks']:
                if block['type'] == 0:
                    text = ' '.join([x['text'] for line in block['lines'] for x in line['spans']])
                    if not line_to_skip(text):
                        line_text.append((index, re.sub(" +", " ", text.strip())))

        return line_text
    
    doc = fitz.open(filename)
    lines = extract_pages(doc)
    save_cp("\n".join([f"{x},{y}" for x, y in lines]), path=filename, fn="raw1.txt")
    
    break_token = "<BREAK>"; break_token2 = "<BREAK2>"
    break_token_patterns = {
        PASAL_PATTERN + "$": break_token,
        BAB_PATTERN + "$": break_token,
        BAGIAN_PATTERN + "$": break_token,
        PARAGRAPH_PATTERN + "$": break_token,
        r"^Menimbang\s*\:.+": break_token,
        r"^Mengingat\s*\:.+": break_token,
        r"^MEMUTUSKAN\s*\:.+": break_token,
        r"^DENGAN\s+RAHMAT\s+TUHAN\s+": break_token,
        r"^Agar\s+setiap\s+orang\s+mengetahuinya": break_token
    }
    
    lines2 = [("","")]
    for idx, (pageidx, line) in enumerate(lines): 
        if idx == 0:
            lines2.append((pageidx, line))

        if re.match(r"(\(\d+\))|(\d+\.)|\d+\)|([a-z]{0,1}+\.)", line) and re.match(r".+[\.:;](\s+((dan\/atau)|(atau)|(dan)))?$", lines[idx-1][1].strip()):
            lines2.append((pageidx,break_token2))

        for pattern, token in break_token_patterns.items():
            if re.match(pattern, line):
                lines2.append((pageidx,token))
                
        if re.match(r"^((Menimbang)|(Mengingat)|(MEMUTUSKAN))\s*:.*", line):
            found = re.search(r"^((Menimbang)|(Mengingat)|(MEMUTUSKAN))\s*:", line)
            lines2.append((pageidx,break_token))
            lines2.append((pageidx, line[:found.span()[1]].strip()))
            lines2.append((pageidx,break_token))
            lines2.append((pageidx, line[found.span()[1]:].strip()))  
        elif len(line)>0:
            lines2.append((pageidx, line))
        else:
            lines2.append((pageidx, break_token))

        if re.match(r"^Pasal\s+\d+$", line):
            lines2.append((pageidx, break_token))
    
    save_cp("\n".join([f"{x},{y}" for x, y in lines2]), path=filename, fn="raw2.txt")
    final_text = []
    for idx, (pageidx, line) in enumerate(lines2):
        if line == break_token or line == break_token2:
            continue
        if idx==0:
            final_text.append(line)
        else:
            if lines2[idx-1][1] == break_token:
                final_text.append(line)
            elif lines2[idx-1][1] == break_token2:
                final_text[-1] += "\n" + line
            else:
                final_text[-1] += " " + line
                
    save_cp("\n".join(final_text), path=filename, fn="final.txt")
    return final_text


# In[893]:


def refine_pasal(block):
    NUM = [r"^\(\d+\)", r"^\d+\)", r"^\d+\.", r"^[a-z]{0,1}+\."]
    NUM_arranged = []
    result = []
    for line in block:
        found = False
        for lvl, num in enumerate(NUM_arranged):
            if re.match(num+".+", line): 
                found = re.search(num, line)
                ref = line[found.span()[0]:found.span()[1]]
                text = line[found.span()[1]:]
                result.append((lvl+1, ref,text))
                found = True
                break

        if not found:
            for num in NUM:
                if re.match(num+".+", line):
                    found = re.search(num, line)
                    ref = line[found.span()[0]:found.span()[1]]
                    text = line[found.span()[1]:]
                    result.append((len(NUM_arranged)+1, ref, text))
                    NUM_arranged.append(num)
                    found = True
                    break

        if not found:
            result.append((0,'',line))

    return result

def refine_heading(line, pattern):
    found = re.search(pattern, line)
    ref = line[found.span()[0]:found.span()[1]]
    text = line[found.span()[1]:]
    return (ref, text)

def to_html(data, output, title = ""):
    doc = dominate.document(title=title)
    
    def get_heading_id(text):
        return "-".join(ref.lower().split())

    with doc.head:
        style("""
                html, h1, h2, h3, h4, h5, h6 {
                     font-size: 13px;
                     font-family: 'Segoe UI'
                }

                html {
                    background-color: #796b6b;
                }
                
                p {
                    margin-block-start: 0.2em;
                    margin-block-end: 0.2em;
                }

                h1, h2, h3, h4, h5, h6 {
                    text-align: center;
                    margin-block-start: 0.4em;
                    margin-block-end: 0.4em;
                }

                .t0 {
                    padding-left: 5px;
                }

                .t1 {
                    padding-left: 10px;
                }

                .t2 {
                    padding-left: 25px;
                }

                .t3 {
                    padding-left: 35px;
                }

                .t4 {
                    padding-left: 45px;
                }

                div.bl{
                    width: 100%;
                }

                p {
                    text-align: justify;
                }

                .container{
                    background-color: white;
                    width:80%; 
                    max-width:1020px;
                    padding:40px;
                    margin: 0 auto;
                }
                
                .fc {
                    display: flex;
                    align-content: space-around;
                }
                
                .cnt {
                    padding-left: 3px;
                }
               
               
                """)


    with doc:
        with div(_class="container"):
            curr_BAB = "none"
            curr_BAGIAN = "none"
            curr_PARAGRAPH = "none"
            curr_PASAL = "none"
            for idx, line in enumerate(data):
                if len(line) ==0:
                    continue
                if re.match(BAB_PATTERN+".+", line):
                    ref, text = refine_heading(line, BAB_PATTERN)
                    curr_BAB = get_heading_id(ref)
                    curr_BAGIAN = "none"
                    curr_PARAGRAPH = "none"
                    with div(id=get_heading_id(ref),_class="bl hd").add(h3()):
                        span(ref)
                        br()
                        span(text)
                elif re.match(BAGIAN_PATTERN+".+", line):
                    ref, text = refine_heading(line, BAGIAN_PATTERN)
                    curr_BAGIAN = get_heading_id(ref) 
                    curr_PARAGRAPH = "none"
                    with div(id=get_heading_id(ref),_class="bl hd", bab=curr_BAB).add(h4()):
                        span(ref)
                        br()
                        span(text)
                elif re.match(PARAGRAPH_PATTERN+".+", line):
                    ref, text = refine_heading(line, PARAGRAPH_PATTERN)
                    curr_PARAGRAPH = get_heading_id(ref) 
                    with div(id=get_heading_id(ref),_class="bl hd", bab=curr_BAB, bagian=curr_BAGIAN).add(h5()):
                        span(ref)
                        br()
                        span(text)
                elif re.match(PASAL_PATTERN, line):
                    ref, text = refine_heading(line, PASAL_PATTERN)
                    curr_PASAL = get_heading_id(ref)
                    div(id=get_heading_id(ref),_class="bl hd", bab=curr_BAB, bagian=curr_BAGIAN, paragraf=curr_PARAGRAPH).add(h6(line))       
                elif line.isupper() or re.match(r"^((Menimbang)|(Mengingat)|(MEMUTUSKAN))\s*:.*", line):
                    div(_class="bl meta").add(h2(line))
                else:
                    refined = refine_pasal(line.split('\n'))
                    if re.match(PASAL_PATTERN, data[idx-1]):
                        for lvl, ref, text in refined:
                            with div(_class=f"bl t{lvl} fc", id=ref, pasal=curr_PASAL):
                                div(_class="pre").add(p(ref))
                                div(_class="cnt").add(p(text))
                                
                    elif re.match("^Menimbang\s*:", data[idx-1]):
                        for lvl, ref, text in refined:
                            with div(_class=f"bl t{lvl} fc", id=ref, tipe="menimbang"):
                                div(_class="pre").add(p(ref))
                                div(_class="cnt").add(p(text))
                                
                    elif re.match("^Mengingat\s*:", data[idx-1]):
                        for lvl, ref, text in refined:
                            with div(_class=f"bl t{lvl} fc", id=ref, tipe="mengingat"):
                                div(_class="pre").add(p(ref))
                                div(_class="cnt").add(p(text))
                                
                    elif re.match("^MEMUTUSKAN\s*:", data[idx-1]):
                        for lvl, ref, text in refined:
                            with div(_class=f"bl t{lvl} fc", id=ref, tipe="memutuskan"):
                                div(_class="pre").add(p(ref))
                                div(_class="cnt").add(p(text))
                                
                    else:
                        for lvl, ref, text in refined:
                            with div(_class=f"bl t{lvl} fc"):
                                div(_class="pre").add(p(ref))
                                div(_class="cnt").add(p(text))          

    with open(output,'w', encoding='utf-8') as f:
        f.write(doc.render())


# In[894]:


fn = "PERATURAN/PMK/Peraturan Menteri Keuangan Nomor  209~PMK.05~2020 Tahun 2020.pdf"
data = exctract_reg_text(fn)
to_html(data, "PMK 209~2020.html")


# In[ ]:




