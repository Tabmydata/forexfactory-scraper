import csv
import json
import sys

IMPACT_MAP = {
    'High Impact Expected': 'High',
    'Medium Impact Expected': 'Medium',
    'Low Impact Expected': 'Low',
    'Holiday': 'Holiday',
    'Non-Economic': 'Holiday',
}

def convert(input_csv, output_json):
    events = []
    with open(input_csv, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            events.append({
                'title':    row['Event'].strip(),
                'country':  row['Currency'].strip().upper(),
                'date':     row['DateTime'].strip(),
                'impact':   IMPACT_MAP.get(row['Impact'].strip(), 'Low'),
                'forecast':    row['Forecast'].strip(),
                'previous':    row['Previous'].strip(),
                'actual':      row['Actual'].strip(),
                'actual_dir':  row.get('ActualDir', '').strip(),
                'detail':      row.get('Detail', '').strip(),
                'url':         row.get('Url', '').strip(),
            })

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

    print(f'Done: {len(events)} events → {output_json}')

if __name__ == '__main__':
    input_csv  = sys.argv[1] if len(sys.argv) > 1 else 'output.csv'
    output_json = sys.argv[2] if len(sys.argv) > 2 else 'econ_thisweek.json'
    convert(input_csv, output_json)
