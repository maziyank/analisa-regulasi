import PyPDF2
import re

class UUParser:
    def __init__(self, file):        
        self.__text = ""
        if file: self.load_pdf(file)
        
    def load_pdf(self, file):
        pdfFileObj = open(file, 'rb') 
        pdfReader = PyPDF2.PdfFileReader(pdfFileObj, strict=False) 

        text = ''
        for i in range(pdfReader.numPages):
            pageObj = pdfReader.getPage(i) 
            text += ' '+ pageObj.extractText()

        self.__text = self.clean_text(text)              
        pdfFileObj.close() 
        
    def clean_text(self, text):
        text = text.replace('\n','')
        text = re.sub(' +', ' ', text)
        text = re.sub('-\s{0,1}\d+\s{0,1}-', '', text)   
        text = re.sub('(\d{4},\sNo.\d+)', '', text)           
        
        return text
        
    def get_text(self):
        return self.__text
    
    def get_phylosophical_consideration(self):
        cr = re.compile(r"menimbang\s{0,}\:(.+)(mengingat)", re.MULTILINE|re.IGNORECASE)
        cd = cr.search(self.__text).groups(0)[0].strip()
        cd = cd.split(';')
        cd = [c.strip() for c in cd]
        cd = [c for c in cd if len(c)>0]
                
        res = []
        for tx in cd:
            num = re.match(r"^[a-z]\.", tx)     
            if num: 
                b = num.group(0)
                res.append((b.replace('.','').strip(), tx.replace(b, '').strip()))               
            else:
                res.append((None, tx))
        
        return res
    
    def get_legal_consideration(self):
        cr = re.compile(r"mengingat\s{0,}\:(.+)(Dengan\s+Persetujuan)", re.MULTILINE|re.IGNORECASE)
        cd = cr.search(self.__text).groups(0)[0].strip()
                
        cd = cd.split(';')
        cd = [c.strip() for c in cd]
        cd = [c for c in cd if len(c)>0]
                
        res = []
        for tx in cd:
            num = re.match(r"^[a-z]\.", tx)     
            if num: 
                b = num.group(0)
                res.append((b.replace('.','').strip(), tx.replace(b, '').strip()))               
            else:
                res.append((None, tx))
        
        return res
        
    def get_title(self):
        cr = re.compile(r"tentang(.+)dengan rahmat", re.MULTILINE|re.IGNORECASE)
        
        return cr.search(self.__text).groups(0)[0].strip()


