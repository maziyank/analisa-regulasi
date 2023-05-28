from os import walk
import json
import re
from pdfminer.high_level import extract_text

class UUParser:
    """ Indonesian Bill Text Parser.
        Parsing Bill published in PDF.          
    """                

    def __init__(self, file, parse_now: bool = False):        
        self.__text = ""
        self.rawtext = ""
        if file: self.load_pdf(file, parse_now)


    def load_pdf(self, file: str, parse_now: bool = True):
        """ Load PDF from PDF. 
        Reccomend loading a bill from official gazette (peraturan.go.id)

        Args:
            file ([str]): filename
        """

        text = extract_text(file)
        self.rawtext = text
        if parse_now:
            self.__text = self.clean_text(text)       
                    
            self.header, self.body= self.split_heading_and_body(self.__text)          
            self.title = self.get_title()
            self.parsed_text = self.parse_body(self.body)

        
    def get_rawtext(self):
        """ Get Raw Text
        
        Args: None

        Return:
        [type] : Original text
        """

        return self.rawtext

    def clean_text(self, text: str):
        """ Clean Bill Text 

        Args:
            text (str): Loaded text

        Returns:
            [type]: Clean Text
        """        

        # remove unknown character
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', '', text)      
        text = re.sub('\s+(\.\s?){3}','...', text)

        # remove common unnecessary part
        text = text.split('\n')
        temp = []
        for t in text:
            if "PRESIDEN" in t.strip():
               continue
            if "REPUBLIK INDONESIA" in t.strip():
               continue
            if re.match("SK\s+No\s+\d+.+?A", t):
               continue
            if re.match("\w\.{3}$", t.strip()):
               continue
            if re.match("^www.+\.go\.id$", t.strip()):
               continue
            if re.match("^-\s{0,3}\d+\s{0,3}-$", t.strip()):
               continue
            if re.match("(\d{4},\sNo.\d+)", t.strip()):
               continue 

            temp.append(re.sub(' +', ' ', t))

        text = ' '.join(temp) 

        return text

    def split_heading_and_body(self, text):        
        """ Split bill heading and body text  

            Returns:
                [(str, body)]: (Heading, Body)
        """

        text = re.search(r"Menetapkan\s*:[^\.]*\.*?", text)
        return (self.__text[:text.span()[1]+1], self.__text[text.span()[1]+1:])

    def parse_body(self, body):
        """ Parse body structure  

            Returns:
                [(id, text))]: (Section Title, Text)
        """

        is_amandement = 'perubahan atas' in self.title.lower()
        
        
        chunks = [body]
        rs = []
        if is_amandement:
            rs.extend([
                re.compile(r"((Pasal\sI).+?((?=\s+Pasal\sII)))|((Pasal\sII).+?((?=$|\s+Pasal\sI)))"),
                re.compile(r"""(\d+\.\s{0,3}(Judul|Ketentuan|Di\s+antara).+?berbunyi\s+sebagai\s+berikut\s?:)|(\d+\.\s{0,3}Ketentuan\sPasal\s\w+\sdihapus)|(\d+\.\s{0,3}Pasal\s).+?((tercantum|ditetapkan)\s+dalam\s+penjelasan(\s+pasal\s+demi\s+pasal\s+([Uu]ndang-[Uu]ndang\s+ini)?)?\.?)""")
            ]) 

        rs.extend([
            re.compile(r"(BAB\s.+?(?=$|(\sBAB)))"),
            re.compile(r"(Bagian\s+Ke.+?(?=$|(\sBagian\s+Ke.+)))"),
            re.compile(r"(Paragraf\s+\d+.+?(?=$|(\sParagraf\s+\d+)))"),
            re.compile(r"(((?<!dalam)\sPasal\s\d+).+?)(?=$|(?<!dalam)\sPasal\s\d+)")
            ])

        
        for index, r in enumerate(rs):
            temp = chunks.copy(); chunks = []
            for text in temp:
                if "$AmmendedItem=>" in text: 
                    chunks.append(text.strip())
                else:
                    while match := re.search(r, text):
                        chunks.append(text[:match.span()[0]].strip())
                        found = text[match.span()[0]:match.span()[1]]
                        if index != 1:
                            chunks.append(found.strip())
                        else:
                            chunks.append(f"$AmmendedItem=> {found.strip()}")
                        text = text[match.span()[1]:]
                    if len(text.strip())>0:
                        chunks.append(text.strip())

        chunks = [x for x in chunks if len(x)>0]
        
        rs2 = [
            re.compile(r"(^Pasal\sI+(?=\s))"),
            re.compile(r"(^\$AmmendedItem=>(?=\s))"),
            re.compile(r"(^BAB\s[A-Z]+(?=\s))"),
            re.compile(r"(^Bagian\sKe\w+(?=\s))"),
            re.compile(r"(^Paragraf\s\d+(?=\s))"),
            re.compile(r"(^Pasal\s\d+(?=\s))") if not is_amandement else re.compile(r"(^\"?Pasal\s\d+[A-Z]?(?=\s))"),        
        ]

        parsed_data = []
        for text in chunks:
            for i, r in enumerate(rs2):
                if re.match(r, text):
                    splited_text = [x.strip() for x in re.split(r, text, maxsplit=1) if len(x)>0]
                    parsed_data.append(tuple(splited_text))
                    break
                if i==len(rs2) - 1:
                    parsed_data.append(("Unknown", text))
                

        return parsed_data

    def info(self):
        """ Retrieve general information about the bill (number, year, enacment etc.)

        Returns:
            [dict]: number, year, signed_date and enactment_date
        """

        result = dict()

        # extract number and year
        cr = re.compile(r"(UNDANG-UNDANG)|(PERATURAN PEMERINTAH)|(PERATURAN PRESIDEN) REPUBLIK INDONESIA NOMOR\s(\d+)\sTAHUN\s(\d{4})", re.MULTILINE|re.IGNORECASE)
        if res := cr.search(self.header):
            numberyear = res.groups(0)
            result['number'] = int(numberyear[0]) if numberyear[0].isdigit() else numberyear[0]
            result['year'] = int(numberyear[1]) if numberyear[1].isdigit() else numberyear[1]
        else:
            result['number'] = None               
            result['year'] = None              

        # extract signed date
        cr2 = re.compile(r"disahkan\s+di\s+(.+)\spada\stanggal\s(\d+\s\w+\s\d{4})\sPresiden", re.MULTILINE|re.IGNORECASE)        
        if res2 := cr2.search(self.body):
            signed_date = res2.groups(0)[1]
            result['signed_date'] = int(signed_date) if signed_date.isdigit() else signed_date
        else:
            result['signed_date'] = None            

        # extract enactment date
        cr3 = re.compile(r"diundangkan\s+di\s+(.+)\spada\stanggal\s(\d+\s\w+\s\d{4})", re.MULTILINE|re.IGNORECASE)
        if res3 := cr3.search(self.body):
            enactment_date = res3.groups(0)[1]
            result['enactment_date'] = int(enactment_date) if enactment_date.isdigit() else enactment_date
        else:
            result['enactment_date'] = None

        # extract effective date
        cr4 = re.compile(r"(Undang-Undang)|(Peraturan Pemerintah)|(Peraturan Presiden) ini mulai berlaku pada\stanggal\s(\d+\s\w+\s\d{4})", re.MULTILINE|re.IGNORECASE)
        if res4 := cr4.search(self.body):            
            effective_date = res4.groups(0)[0]
            result['effective_date'] = int(effective_date) if effective_date.isdigit() else effective_date
        else:
            result['effective_date'] = result['enactment_date'] 

        # extract that the bill is amandement or not
        result['is_amandement'] = 'perubahan atas' in self.title.lower()
        
        return result
        
    def get_text(self):
        """ Retrieve bill full text  

            Returns:
                [str]: (Full Text)
        """

        return self.__text

    def get_articles(self):
        """ Retrieve bill articles  

            Returns:
                [str]: (Article Text)
        """

        articles = [x for x in self.parsed_text if "Pasal" in x[0]]
        
        return articles

    def get_header(self):
        """ Retrieve bill heading text  

            Returns:
                [str]: (Heading Text)
        """

        return self.header

    def get_body(self):
        """ Retrieve bill body text  

            Returns:
                [str]: (Body Text)
        """        

        return self.body

    def get_definitions(self):                
        """ Parsing Definitions used in the Bill

        Returns:
            [list]: (List of definitions)
        """         
        r1 = re.compile(r"^(.+)( adalah )", re.IGNORECASE);
        r2 = re.compile(r"(disingkat|(disebut)|disingkat,|disebut,)(.+)", re.IGNORECASE);

        definitions = []
        for id, text in self.get_articles():
            chunks = []
            
            while match := re.search("(\d+\.\s+.+?)(?=$|\d+\.\s+\D)", text):
                chunks.append(text[:match.span()[0]].strip())
                found = text[match.span()[0]:match.span()[1]]
                chunks.append(re.sub("^\d+\.\s+", "", found.strip()))
                text = text[match.span()[1]:]
            if len(text.strip())>0:
                chunks.append(text.strip())

            for chunk in chunks:
                if res1 := r1.search(chunk):
                    found = res1.groups(0)[0].strip()
                    if res2 := r2.search(found):
                        found = res2.groups(0)[2].strip()                    
                    
                    definitions.append((id, found, chunk.strip()))
            

        return definitions

    
    def get_philosophical_consideration(self):
        """ Parsing Philosophical Consideration

        Returns:
            [(str, str)]: (Number and Consideration Text)
        """        

        cr = re.compile(r"menimbang\s*\:(.+)mengingat", re.MULTILINE|re.IGNORECASE)
        consideration = cr.findall(self.header)[0].strip()
        consideration = consideration.split(';')
        consideration = [c.strip() for c in consideration]
        consideration = [c for c in consideration if len(c)>0]
                
        res = []
        for txt in consideration:
            num = re.match(r"^[a-z]\.", txt)     
            if num: 
                b = num.group(0)
                res.append((b.replace('.','').strip(), txt.replace(b, '').strip()))               
            else:
                res.append((None, txt))
        
        return res
    
    def get_legal_consideration(self):
        """ Parsing Legal Consideration

        Returns:
            [(str, str)]: (Number and Consideration Text)
        """      

        cr = re.compile(r"mengingat\s*\:(.+)Dengan\s+Persetujuan", re.MULTILINE|re.IGNORECASE)
        consideration = cr.findall(self.header)[0].strip()        
                
        consideration = consideration.split(';')
        consideration = [c.strip() for c in consideration]
        consideration = [c for c in consideration if len(c)>0]
                
        res = []
        for txt in consideration:
            num = re.match(r"^\d+\.", txt)     
            if num: 
                b = num.group(0)
                res.append((b.replace('.','').strip(), txt.replace(b, '').strip()))               
            else:
                res.append((None, txt))
        
        return res
        
    def get_title(self):
        """ Parsing Bill Title

        Returns:
            [str]: Title
        """      

        cr = re.compile(r"tentang(.+)dengan rahmat", re.MULTILINE|re.IGNORECASE)
        
        return cr.findall(self.header)[0].strip()


    def get_words(self, n = -1, exclude_stopword=False):           
        """ Get token/words appear in the text.

        Args:
            n (int): number of retrieved words
            exclude_stopword (bool, optional): If false will include stopword in the result. Defaults to False.

        Returns:
            [list(tuple)]: list of word and frequency of occurence
        """

        dict_counts = dict()
        words = self.__text.split()

        for w in words:
            w = w.lower().strip().strip('.')            
            if w.isdigit(): continue
            if w in dict_counts: dict_counts[w] += 1
            else: dict_counts[w] = 1
        
        # exclude numbering and bullets                
        for w in list(dict_counts.keys()):
            if re.match(r"([a-z]\.)|([a-z]\))|(\([a-z]\))|(\d+\.)|(\d+\))|(\(\d+\))",w):
                del dict_counts[w]

        # exclude single character
        for w in list(dict_counts.keys()):
            if len(w) == 1:
                del dict_counts[w]                

        # exclude stopword             
        if not exclude_stopword:
            with open('stopwords.txt', 'r') as f:                
                stopword = f.read().splitlines()                                
                for w in list(dict_counts.keys()):
                    if w in stopword: 
                        del dict_counts[w]
        
        # check if n is not defined, then return all words
        if n == -1: n = len(words)

        return sorted(dict_counts.items(), reverse=True, key=lambda x: x[1])[:n]

    def generate_ngrams(self, text, n = 2):
        text = text.lower()
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        tokens = [token for token in text.split(" ") if token != ""]
        ngrams = zip(*[tokens[i:] for i in range(n)])
        return [" ".join(ngram) for ngram in ngrams]        

    def get_phrashes(self, max_word=5, min_occurence=2):
        """ Get Phrasaes in the Bill using n-gram

        Arguments:
            max_word : number of words, default 5
            min_occurence : filter phrases by its occurences, default 2

        Returns:
            [(str, int)]: (List of tuple of Phrases and Occurences)
        """  
                
        phrases = []
        preposition = ['dan','atau','yang','dan/atau','dalam','di','pada','untuk','sebagaimana','atas','bawah','dapat',
        'sesuai','saat','paling','oleh','dari','meliputi','terdiri','serta','dengan','ini','lain','dimaksud','maksud',
        'berdasarkan','tentang','berupa','sejak','paling','tetapi','namun','melainkan','tapi','kecuali','terdapat','ada',
        'ayat','pasal','huruf', 'selanjutnya','sebelumnya','adalah','sebagai','disebut','disingkat','secara','melalui']

        for i in range(2, max_word + 1):
            phrases.extend(self.generate_ngrams(text = self.__text, n = i))

        dict_counts = dict()       
        for p in phrases:
            p = p.lower().strip().strip('.')                        
            if p in dict_counts: dict_counts[p] += 1
            else: dict_counts[p] = 1

        for k in list(dict_counts.keys()):
            if dict_counts[k] < min_occurence:
                del dict_counts[k]
                continue

            token = k.split()
            if (token[0] in preposition) or (token[-1] in preposition):
                del dict_counts[k]
                continue

            if (token[0].isdigit()) or (token[-1].isdigit()):
                del dict_counts[k]
                continue                     

        return sorted(dict_counts.items(), reverse=True, key=lambda x: x[1])

    def get_heading(self):
        """ Get Bill's Heading 

        Returns:
            [(str)]: (List of Heading)
        """  

        heading = [x for x in self.parsed_text if "Pasal" not in x[0]]   

        return heading

    def get_further_provision(self):
        """ Get Further Permission mandated by the Bill

        Returns:
            [(str, str)]: (List of Further Permission)
        """     

        r = re.compile(r"(Ketentuan lebih lanjut mengenai)(.*)((dituangkan dalam)|(diatur dengan)(.*))")
        provisions = []
        for id, sentence in self.parsed_text:
            if found := r.search(sentence):
                found = found.groups(2)
                found = (found[1].strip().split("sebagaimana dimaksud")[0], found[5].strip())
                provisions.append((id, found))

        return provisions

    def extract_currency(self):
        cr1 = re.compile(r"(Rp)([+-]?[0-9]{1,3}(\.?[0-9]{3})*)(,[0-9]{1,4})")
        cr2 = re.compile(r"(USD)([+-]?[0-9]{1,3}(,?[0-9]{3})*)(\.[0-9]{1,4})")

        currencies = []
        for id, sentence in self.parsed_text:
            if found := cr1.search(sentence):
                currencies.append((id, found.group(0)))
            if found2 := cr2.search(sentence):
                currencies.append((id, found2.group(0)))                

        return currencies


    def extract_percent(self):
        cr = re.compile(r"([+-]?[0-9]{1,3}(\.?[0-9]{3})*)%")

        percents = []
        for id, sentence in self.parsed_text:
            if found := cr.search(sentence):
                percents.append((id, found.group(0)))

        return percents        

    def extract_withdraw_provision(self):
        cr = re.compile(r"Pada saat Undang-Undang ini mulai berlaku(.*)dicabut dan dinyatakan")
        result = []
        for id, sentence in self.parsed_text:
            if found := cr.search(sentence):
                result.append((id, found.group(1).strip(', :')))        

        return result

    def to_json(self):
        result = dict()
        result['title'] = self.title
        result['info'] = self.info
        result['philosophical_consideration'] = self.philosophical_consideration
        result['legal_consideration'] = self.legal_consideration
        result['definitions'] = self.definitions
        result['heading'] = self.heading
        result['further_provision'] = self.further_provision
        result['currency'] = self.extract_currency()
        result['percent'] = self.extract_percent()
        result['words'] = self.get_words()
        result['phrases'] = self.get_phrashes()

        return json.dumps(result)