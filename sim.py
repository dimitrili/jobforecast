
import random as rd
import csv
from collections import defaultdict
import datetime as dt

inputfilename = 'testdata.csv'
outputfilename = 'demand.csv'
lqfilename = 'livequote.csv'

# Client's name and budget
client_info = {'clientA': 550000, 'clientB': 140000}
types = ['PB', 'HB', 'SS', 'Others']
formats = ['A', 'A4', 'AB', 'B', 'B+', 'C', 'C+', 'Other']
pps = ['48', '144', '288', '432', '576']
qtys = ['1000', '2000', '3000', '5000', '10000', '15000']
embs = ['Illustration', 'Lam?', 'Foil?', 'UV?', 'Emboss?']

est_year = '2018'
est_month = '08'
history_year = '2015'


def nested_dict(n):
    if n == 1:
        return defaultdict(dict)
    else:
        return defaultdict(lambda: nested_dict(n - 1))


def isdatematch(datestr, m, y):
    """
    to verify if the date is matching, for month and year
    datestr: date string
    m: month string
    y: year string
    """
    if ('/' in datestr):
        d = dt.datetime.strptime(datestr, "%d/%m/%Y")

    elif ('-' in datestr):
        d = dt.datetime.strptime(datestr, "%Y-%m-%d")

    if ((d.year == int(y)) and (d.month == int(m))):
        return True
    else:
        return False


def translatetype(t):
    """
    to translate binding to category code
    """
    if t[0] == 'H':
        return 'HB'
    if (t[0] == 'P'):
        return 'PB'
    if (t[0] == 'S'):
        return 'SS'
    if (t[0] == 'O'):
        return 'Others'


def translatefromrange(inputstr, range):
    """
    to translate inputstr from the range
    """
    temp = range[0]
    for i in range:
        if (int(inputstr) <= int(i)):
            break
        else:
            temp = i
    return temp


def stockcodemapping(s):
    """
    to map the stock code, from stockmapping.csv
    """
    with open('stockmapping.csv', 'r') as stockfile:
        reader = csv.DictReader(stockfile)
        for line in reader:
            if (s == line['Prism papercode']):
                s = line['new code']
                break
    return s


def getthestock(c, t, f):
    """
    to get the stock list and the count under the client's category and format
    c: client's data file name
    t: category
    f: format
    return: dict{stockname: count}
    """
    stock_list = ()
    stock_count = []
    with open(c, 'r') as jobdatafile:
        reader = csv.DictReader(jobdatafile)
        for line in reader:
            index = 0
            if ((line['Binding Cat.'] == t) and (line['Format'] == f)):
                if (line['Text Stock Code '] not in stock_list):
                    stock_list = stock_list + (line['Text Stock Code '],)
                    stock_count.append(0)
                index = stock_list.index(line['Text Stock Code '])
                stock_count[index] += 1
    return dict(zip(stock_list, stock_count))


results = nested_dict(4)
# prepare the new file
newheader = ['Client', 'Binding Cat.', 'Format',
             'PP', 'Qty', 'Embossment', 'Job Amount', 'Text Stock Code ']
with open(outputfilename, 'w', newline='') as new_file:
    csv_writer = csv.writer(new_file)
    csv_writer.writerow(newheader)

for client_name in client_info.keys():
    client_budget = client_info[client_name]
    total_num_jobs = 0
    total_job_amount = 0
    total_job_qty = 0
    copy_unit_price = 0
    # initialize results {} to store data
    for t in types:
        for f in formats:
            for p in pps:
                for q in qtys:
                    # 'jobs' to record how many jobs
                    results[t][f][p][q]['jobs'] = 0
                    # 'amount' to record how much for this type
                    results[t][f][p][q]['amount'] = 0
                    for e in embs:
                        results[t][f][p][q][e] = 0

    with open(inputfilename, 'r') as jobdatafile:
        reader = csv.DictReader(jobdatafile)
        with open(client_name + '.csv', 'w', newline='') as new_file:
            csv_writer = csv.writer(new_file)
            # write the header
            csv_writer.writerow(reader.fieldnames)
            for line in reader:
                a = float(line['Job Amount'].replace(",", ""))
                d = dt.datetime.strptime(line['Add Date'], '%d/%m/%Y %H:%M')
                # only get the client's row and the month we need
                if (isdatematch(str(d.date()), est_month, history_year) and (line['Client Code'] == client_name) and (a != 0) and (line['PP'] != 0)):
                    total_num_jobs += 1
                    total_job_amount += a
                    csv_writer.writerow(line.values())
                    t = line['Binding Cat.']
                    f = line['Format']
                    # calculate the PP range
                    p = translatefromrange(line['PP'], pps)
                    # calculate the qty range
                    q = line['Job Qty'].replace(",", "")
                    total_job_qty += int(q)
                    q = translatefromrange(q, qtys)
                    results[t][f][p][q]['jobs'] += 1
                    # collect the emboss range
                    for temp in embs:
                        if (line[temp] == 'TRUE'):
                            results[t][f][p][q][temp] += 1
                    # collect the Illustration info
                    if (line['Illustration'] == 'Y'):
                        results[t][f][p][q]['Illustration'] += 1

        # calculate the rates for each single type
        for t in types:
            for f in formats:
                for p in pps:
                    for q in qtys:
                        # calculate the rates for the emboss
                        if (results[t][f][p][q]['jobs']):
                            for e in embs:
                                results[t][f][p][q][e] /= results[t][f][p][q]['jobs']
                        if (total_num_jobs):
                            results[t][f][p][q]['jobs'] /= total_num_jobs
                            results[t][f][p][q]['amount'] = results[t][f][p][q]['jobs'] * \
                                client_budget

        # accumulate the rates for each single type
        temp = 0
        for t in types:
            for f in formats:
                for p in pps:
                    for q in qtys:
                        results[t][f][p][q]['jobs'] += temp
                        temp = results[t][f][p][q]['jobs']
    if (total_job_qty):
        copy_unit_price = total_job_amount / total_job_qty
    total_job_amount = 0
    temp = 0
    lq_jobs = 0
    with open(outputfilename, 'a', newline='') as new_file:
        csv_writer = csv.writer(new_file)
        # before generating random jobs, search jobs from the live quote
        with open(lqfilename, 'r') as lqdatafile:
            reader = csv.DictReader(lqdatafile)
            for line in reader:
                if ((line['Customer#'] == client_name) and (isdatematch(line['Ex-Works Date'], est_month, est_year))):
                    t = translatetype(line['Binding'])
                    f = line['Format']
                    p = line['#Text Pages']
                    q = line['Qty']
                    s = line['Text Stock Code'].replace(' ', '')
                    s = stockcodemapping(s)
                    a = float(line['Selling Price'])
                    emblist = ['from live quote']  # TBC
                    rowdata = [client_name, t, f, p, q, emblist, a, s]
                    csv_writer.writerow(rowdata)
                    lq_jobs += 1
                    p = translatefromrange(p, pps)
                    try:
                        # data in live quote might not be in the previous record
                        if (results[t][f][p][q]['amount'] > 0):
                            results[t][f][p][q]['amount'] -= a
                    except KeyError:
                        # print('this job type is not in the previous record')
                        pass
                    total_job_amount += a
        while (total_job_amount < client_budget):
            # get a random job
            temp_rate = rd.random()
            found = False
            for t in types:
                if found:
                    break
                for f in formats:
                    if found:
                        break
                    for p in pps:
                        if found:
                            break
                        for q in qtys:
                            if (temp_rate <= results[t][f][p][q]['jobs']):
                                found = True
                                # verify the type amount
                                if (results[t][f][p][q]['amount'] <= 0):
                                    break
                                # check the emboss and randomly get one
                                emblist = []
                                for e in embs:
                                    if (results[t][f][p][q][e] != 0):
                                        emb_rate = rd.random()
                                        if (emb_rate <= results[t][f][p][q][e]):
                                            emblist.append(e)
                                # check the stock and randomly get one
                                temp_stock = {}
                                temp_stock = getthestock(
                                    client_name + '.csv', t, f)
                                s = rd.choices(list(temp_stock.keys()),
                                               weights=list(temp_stock.values()))
                                s = stockcodemapping(s[0])
                                temp += 1
                                a = copy_unit_price * int(q)
                                results[t][f][p][q]['amount'] -= a
                                rowdata = [client_name, t, f,
                                           p, q, emblist, a, s]
                                csv_writer.writerow(rowdata)
                                total_job_amount += a
                                break
        x = (total_job_amount - client_budget) / client_budget
        print('{}-{} random jobs, {} from live quote, amout:{}, budget:{}, D={:.2f}'.format(client_name, temp, lq_jobs,
                                                                                            total_job_amount, client_budget, x))
    print(client_name + '-unit price => $' + str(copy_unit_price) + '/copy')

print("Simulation of {}-{} is finished!".format(est_year, est_month))
