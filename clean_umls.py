import csv

def rrf_to_csv(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as infile:
        lines = infile.readlines()

    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        csv_writer = csv.writer(outfile)
        
        for line in lines:
            cleaned_line = line.rstrip('|')  
            columns = cleaned_line.split('|')  
            
            # write split data as a row in the CSV file
            csv_writer.writerow(columns)

rrf_to_csv(r"E:\.Neo4jDesktop\relate-data\dbmss\dbms-5a7d22d6-f68d-4cb8-a5c9-0c8032995ed9\import\MRREL.RRF", r"E:\.Neo4jDesktop\relate-data\dbmss\dbms-5a7d22d6-f68d-4cb8-a5c9-0c8032995ed9\import\MRREL.csv")



