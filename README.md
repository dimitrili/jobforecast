# jobforecast
python tool

-source raw data-
1.testdata.csv
2.livequote.csv
3.stockmapping.csv

-output file-
1.demand.csv

-temp file-
1."client's name".csv

---work flow---
1.set the month, year, client's name and budget
2.based on testdata.csv, extract the records of the assigned period
3.calculate the rate for each job type
4.randomly generate the jobs for the month, but search the jobs from livequote.csv first
5.output demand.csv and print out some info



