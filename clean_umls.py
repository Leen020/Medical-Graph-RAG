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

# rrf_to_csv(r"D:\2024AA\META\MRCONSO.RRF", r"C:\Users\LENOVO\Desktop\Marmara_University\7th_semester\graduation project\dataset_extraction_test\MIMIC-IV\hosp\umls\MRCONSO.csv")
# rrf_to_csv(r"D:\2024AA\META\MRREL.RRF", r"C:\Users\LENOVO\Desktop\Marmara_University\7th_semester\graduation project\dataset_extraction_test\MIMIC-IV\hosp\umls\MRREL.csv")
# rrf_to_csv(r"D:\2024AA\META\MRSTY.RRF", r"C:\Users\LENOVO\Desktop\Marmara_University\7th_semester\graduation project\dataset_extraction_test\MIMIC-IV\hosp\umls\MRSTY.csv")
#rrf_to_csv(r"D:\2024AA\META\MRSAT.RRF", r"C:\Users\LENOVO\Desktop\Marmara_University\7th_semester\graduation project\dataset_extraction_test\MIMIC-IV\hosp\umls\MRSAT.csv")
#rrf_to_csv(r"D:\2024AA\META\MRHIER.RRF", r"C:\Users\LENOVO\Desktop\Marmara_University\7th_semester\graduation project\dataset_extraction_test\MIMIC-IV\hosp\umls\MRHIER.csv")
#rrf_to_csv(r"D:\2024AA\META\MRDEF.RRF", r"C:\Users\LENOVO\Desktop\Marmara_University\7th_semester\graduation project\dataset_extraction_test\MIMIC-IV\hosp\umls\MRDEF.csv")
#rrf_to_csv(r"D:\2024AA\META\MRCUI.RRF", r"C:\Users\LENOVO\Desktop\Marmara_University\7th_semester\graduation project\dataset_extraction_test\MIMIC-IV\hosp\umls\MRCUI.csv")
rrf_to_csv(r"C:\Users\LENOVO\Desktop\Marmara_University\7th_semester\graduation project\datasets\2024AB\META\MRXW_TUR.RRF", r"C:\Users\LENOVO\Desktop\Marmara_University\7th_semester\graduation project\datasets\umls\MRXW_TUR.csv")


