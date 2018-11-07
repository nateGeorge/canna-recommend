import analytical360.scrape_360 as sc3
import pandas as pd
import matplotlib.pyplot as plt

def get_unique_chems(nested_list):
    '''
    flattens list and gets all unique chemicals

    args: takes list of lists (i.e. terpenes, cannabinoids), where each entry is
    a string like '34.34% THC'
    returns: set of unique chemicals from the list
    '''
    unique = set()
    for l in nested_list:
        for r in l:
            stuff = r.split('%')
            chem = stuff[-1].strip()
            if chem not in unique:
                unique = unique | set([chem])

    return unique

''' terpenes:
beta-Pinene
Humulene
Limonene
alpha-Pinene
Caryophyllene
Beta Pinene
N/A
Linalool
H2O
Caryophyllene oxide
Myrcene
< 0.01 TERPENE-TOTAL
TERPENE-TOTAL
Terpinolene
Ocimene
Alpha Pinene
'''

cannabinoids, terpenes, no_imgs, im_sources, names, clean_names = sc3.load_raw_scrape()

cdict = sc3.parse_raw_scrape(cannabinoids, terpenes, names)

cdf = pd.DataFrame(cdict)

for c in cdf.columns:
    print(c)
    if c == 'name':
        continue

    cdf[c] = pd.to_numeric(cdf[c])

cdf['thc_total'].hist(bins=50)
plt.show()

cdf['cbd_total'].hist(bins=50)
plt.show()
