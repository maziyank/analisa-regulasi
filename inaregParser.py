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
        Reccomend loading Bill published in official gazzete (peraturan.go.id)

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

        # remove year and gazzete number appear in each page
        text = re.sub('(\d{4},\sNo.\d+)', '', text)           
        
        return text
        
    def get_text(self):
        return self.__text
    
    def get_phylosophical_consideration(self):
        """ Parsing Pylosophical Consideartion

        Returns:
            [(str, str)]: (Number and Consideration Text)
        """        

        cr = re.compile(r"menimbang\s{0,}\:(.+)(mengingat)", re.MULTILINE|re.IGNORECASE)
        consideration = cr.search(self.__text).groups(0)[0].strip()
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
        """ Parsing Legal Consideartion

        Returns:
            [(str, str)]: (Number and Consideration Text)
        """      

        cr = re.compile(r"mengingat\s{0,}\:(.+)(Dengan\s+Persetujuan)", re.MULTILINE|re.IGNORECASE)
        consideration = cr.search(self.__text).groups(0)[0].strip()
                
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
        
        return cr.search(self.__text).groups(0)[0].strip()


