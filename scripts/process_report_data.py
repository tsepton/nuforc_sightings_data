from datetime import datetime,timedelta
import click
import json
from csv import DictWriter

REPORT_DATE_TIME = "%m/%d/%y %H:%M"
SHORT_REPORT_DATE_TIME = "%m/%d/%y"

def create_date_time(report_date_time):
    """ Takes a report datetime as a string and converts it into a datetime
        object.
    """
    try:
        date_time = datetime.strptime(report_date_time, REPORT_DATE_TIME)
    except ValueError:
        # Some of the dates are in the "short" format.
        date_time = datetime.strptime(report_date_time, SHORT_REPORT_DATE_TIME)

    # Correct century.
    if date_time > datetime.now():
        date_time = date_time - timedelta(year=100)

    return date_time

@click.command()
@click.argument('raw_report_file', type=click.File('r'))
@click.option('--output-file', '-o', 
              type=click.File('w'), 
              default='output.csv')
@click.option('--exceptions-file', '-e', 
              type=click.File('w'), 
              default='exceptions.json')
def main(raw_report_file, output_file, exceptions_file):
    """ Reads the raw scraped JSON reports and processes them into a CSV file
        whilst performing data enrichment and cleaning. If a report can't be
        cleaned in an automated way it is passed to an exceptions file, with
        the exception added as a field.
    """

    writer = DictWriter(output_file, fieldnames=[
        "summary", "city", "state", "date_time", "shape", "duration",
        "stats", "report_link", "text", "posted"
    ])

    writer.writeheader()

    for report_str in raw_report_file:
        
        report = json.loads(report_str)
        
        try:
            # Standardize the dates into isoformat.
            posted_date_time = \
                create_date_time(report["posted"]).isoformat()
            report_date_time = \
                create_date_time(report["date_time"]).isoformat()
        except Exception as e:
            report["exception"] = str(e)
            exceptions_file.write(json.dumps(report) + "\n")
            continue # Skip to the next record.

        report["posted"] = posted_date_time
        report["date_time"] = report_date_time
        
        # Standardize shapes to lower case, merge the obvious ones.
        report["shape"] = report["shape"].lower() if report["shape"] else None
        if report["shape"] == "triangular":
            report["shape"] = "triangle"
        if report["shape"] == "changed": 
            report["shape"] == "changing"

        # Standardize the state names to upper case.
        report["state"] = report["state"].upper() if report["state"] else None

        # Bad / weird state names.
        # NF -> NL for Newfoundland and Labrador.
        if report["state"] == "NF":
            report["state"] = "NL"
        # PQ -> QC for Quebec.
        if report["state"] == "PQ":
            report["state"] = "QC"
        # SA -> SK for Sasketchewan.
        if report["state"] == "SA":
            report["state"] = "SK"
        # YK -> YT for Yukon Territory.
        if report["state"] == "YK":
            report["state"] = "YT"

        writer.writerow(report)

if __name__ == "__main__":
    main() # Click injects the arguments.