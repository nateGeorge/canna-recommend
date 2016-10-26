import requests
from bs4 import BeautifulSoup as bs

# convert pdf to text easily:
# pdftotext -layout 05_2015_MMR_report.pdf test.txt


# from http://stackoverflow.com/questions/16694907/how-to-download-large-file-in-python-with-requests-py
def download_file(url):
    local_filename = url.split('/')[-1]
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)
    return local_filename

def download_reports(reports):
    for y in reports.keys():
        for d in reports[y]:
            fname = download_file(d)

def parse_pdf(file_n):
    genderWords = set(['Gender', 'Sex'])
    with open(file_n) as f:
        table1 = False
        table1dat = []
        for l in f.readlines():
            words = [i.strip('\n').strip() for i in l.split('  ') if i != '' and i != '\n']
            if len(words) > 0 and words[0] in genderWords:
                table1 = True
            if table1:
                print words
                table1dat.append(words)
                if len(words) == 0:
                    table1 = False
                    table1dat = table1dat[:-2] # get rid of blank line and **

        return table1dat


base_url = 'https://www.colorado.gov/pacific/cdphe/medical-marijuana-statistics-and-data'

req = requests.get(base_url)
soup = bs(req.content, 'lxml')
year_stats = soup.findAll('ul')[1].findAll('li')
reports = {}
for y in year_stats:
    new_url = y.findAll('a')[0].get('href')
    year = new_url.split('/')[-1].split('-')[0]
    new_req = requests.get(new_url)
    new_soup =  bs(new_req.content, 'lxml')
    report_links = new_soup.findAll('ul')[1].findAll('a')
    reports[year] = []
    for r in report_links:
        reports[year].append(r.get('href'))
