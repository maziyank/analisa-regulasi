from os import walk
import PyPDF2
import re

class UUParser:
    """ Indonesian Bill Text Parser.
        Parsing Bill published in PDF.          
    """                

    def __init__(self, file):        
        self.__text = ""
        if file: self.load_pdf(file)
        
    def load_pdf(self, file: str):
        """ Load PDF from PDF. 
        Reccomend loading a bill from official gazette (peraturan.go.id)

        Args:
            file ([str]): filename
        """

        pdfFileObj = open(file, 'rb') 
        pdfReader = PyPDF2.PdfFileReader(pdfFileObj, strict=False) 

        text = ''
        for i in range(pdfReader.numPages):
            pageObj = pdfReader.getPage(i) 
            text += ' '+ pageObj.extractText()
        
        self.__text = self.clean_text(text)       
        self.__heading, self.__body = self.split_heading_and_body(self.__text)   
        self.__sentences = [s.strip() for s in self.__body.split('.')]            
        pdfFileObj.close() 
        
    def clean_text(self, text: str):
        """ Clean Bill Text 

        Args:
            text (str): Loaded text

        Returns:
            [type]: Clean Text
        """        

        # remove new lines
        text = text.replace('\n','')

        # remove double white spaces
        text = re.sub(' +', ' ', text)

        # remove page number
        text = re.sub('-\s{0,1}\d+\s{0,1}-', '', text)   

        # remove year and gazette number appear in each page
        text = re.sub('(\d{4},\sNo.\d+)', '', text)           
        
        return text

    def split_heading_and_body(self, text):        
        """ Split bill heading and body text  

            Returns:
                [(str, body)]: (Heading, Body)
        """
        
        text = re.search(r"Menetapkan\s*:[^\.]*\.*?", text)
        return (self.__text[:text.span()[1]+1], self.__text[text.span()[1]+1:])

    def info(self):
        """ Retrieve general information about the bill (number, year, enacment etc.)

        Returns:
            [dict]: number, year, signed_date and enactment_date
        """

        cr = re.compile(r"UNDANG-UNDANG REPUBLIK INDONESIA NOMOR\s(\d+)\sTAHUN\s(\d{4})", re.MULTILINE|re.IGNORECASE)
        res = cr.search(self.__heading).groups(0)

        cr2 = re.compile(r"disahkan\s+di\s+(.+)\spada\stanggal\s(\d+\s\w+\s\d{4})\sPresiden", re.MULTILINE|re.IGNORECASE)
        res2 = cr2.search(self.__body).groups(0)

        cr3 = re.compile(r"diundangkan\s+di\s+(.+)\spada\stanggal\s(\d+\s\w+\s\d{4})", re.MULTILINE|re.IGNORECASE)
        res3 = cr3.search(self.__body).groups(0)

        return {
            "number": int(res[0]) if res[0].isdigit() else res[0],
            "year": int(res[1]) if res[1].isdigit() else res[1],
            "signed_date": int(res2[1]) if res2[1].isdigit() else res2[1],
            "enactment_date": int(res3[1]) if res3[1].isdigit() else res3[1]
        }
        
    def get_text(self):
        """ Retrieve bill full text  

            Returns:
                [str]: (Full Text)
        """

        return self.__text

    def get_header(self):
        """ Retrieve bill heading text  

            Returns:
                [str]: (Heading Text)
        """

        return self.__heading

    def get_body(self):
        """ Retrieve bill body text  

            Returns:
                [str]: (Body Text)
        """        

        return self.__body 

    def get_definitions(self):                  
        r1 = re.compile(r"^(.+)( adalah )", re.IGNORECASE);
        r2 = re.compile(r"(disingkat|(disebut)|disingkat,|disebut,)(.+)", re.IGNORECASE);

        definitions = []
        for sentence in self.__sentences:
            if res1 := r1.search(sentence):
                found = res1.groups(0)[0].strip()
                if res2 := r2.search(found):
                    found = res2.groups(0)[2].strip()                    
                
                definitions.append(found)

        return definitions

    
    def get_philosophical_consideration(self):
        """ Parsing Philosophical Consideration

        Returns:
            [(str, str)]: (Number and Consideration Text)
        """        

        cr = re.compile(r"menimbang\s*\:(.+)mengingat", re.MULTILINE|re.IGNORECASE)
        consideration = cr.findall(self.__heading)[0].strip()
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
        consideration = cr.findall(self.__heading)[0].strip()        
                
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
        
        return cr.findall(self.__heading)[0].strip()


    def get_words(self, n, exclude_stopword=False):           
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
        if not n: n = len(words)

        return sorted(dict_counts.items(), reverse=True, key=lambda x: x[1])[:n]

    def generate_ngrams(self, text, n = 2):
        text = text.lower()
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        tokens = [token for token in text.split(" ") if token != ""]
        ngrams = zip(*[tokens[i:] for i in range(n)])
        return [" ".join(ngram) for ngram in ngrams]        

    def get_phrashes(self, max_word=5, min_occurence=2):
        phrases = []
        preposition = ['dan','atau','yang','dan/atau','dalam','di','pada','untuk','sebagaimana','atas','bawah','dapat',
        'sesuai','saat','paling','oleh','dari','meliputi','terdiri','serta','dengan','ini','lain','dimaksud','maksud',
        'berdasarkan','tentang','berupa','sejak','paling',
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
        r = re.compile(r"((BAB\s(.+))|(Bagian\s(.+))|(Paragraf\s(.+)))\s((Bagian)|(Pasal)|(Paragraf))");

        chapters = []
        for sentence in self.__sentences:
            if res := r.search(sentence):
                found = res.groups(1)[0]
                found = re.split(r"( Bagian )|( Pasal )|( Paragraf )", found)[0].strip()
                
                chapters.append(found)

        return chapters