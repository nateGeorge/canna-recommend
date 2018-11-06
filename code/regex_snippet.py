"""
regex snippet from analyzing analytical360 data
"""
    for c in cannabinoids:
        for r in c:
            res = re.search('(([\d\.]+).*(thc.*)', r, re.IGNORECASE)
            if res:
                res.group(1)
                thca.append(float(res.group(1)))
                continue
            res = re.search('(([\d\.]+).*thc', r, re.IGNORECASE)
            if res:
                thc.append(float(res.group(1)))
                continue
            res = re.search('(([\d\.]+).*thc', r, re.IGNORECASE)
            if res:
                thc.append(float(res.group(1)))
                continue
            res = re.search('(([\d\.]+).*cbn.*', r, re.IGNORECASE)
            if res:
                cbn.append(float(res.group(1)))
                continue
            res = re.search('(([\d\.]+).*cbd-a.*', r, re.IGNORECASE)
            if res:
                cbda.append(float(res.group(1)))
                continue
            res = re.search('(([\d\.]+).*cbd.*', r, re.IGNORECASE)
            if res:
                cbd.append(float(res.group(1)))
                continue
            res = re.search('(([\d\.]+).*cbd.*', r, re.IGNORECASE)
            if res:
                cbd.append(float(res.group(1)))
                continue
