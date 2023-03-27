# Google Analytics Api
from re import finditer

from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']
KEY_FILE_LOCATION = 'ubbeweb-568d9d7ad493.json'
VIEW_ID = 'ga:177302398'


class GoogleAnalytics:

    def __init__(self):
        """Initializes an Analytics Reporting API V4 service object.

        Returns:
          An authorized Analytics Reporting API V4 service object.
        """
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            KEY_FILE_LOCATION, SCOPES)

        # Build the service object.
        analytics = build('analyticsreporting', 'v4', credentials=credentials)

        self.analytics = analytics

    @staticmethod
    def slice_per(source, step):
        return [source[x:x + step] for x in range(0, len(source), step)]

    @staticmethod
    def camel_case_split(identifier):
        matches = finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
        return [m.group(0).capitalize() for m in matches]

    @staticmethod
    def camel_case_join(words: list):
        new_word = ""
        for word in words:
            new_word += word + " "
        return new_word.strip()

    def query(self, start_date: str, end_date: str, metrics: list, dimensions: list):
        """
        :param start_date: Year-Month-Day
        :param end_date: Year-Month-Day
        :param metrics: Google analytics measurements (sessions)
        :param dimensions: Google analytics measurements (country)
        :return:
        """
        end_date_formatted = 'today' if end_date == 'today' else end_date
        metrics_list = []
        dimensions_list = []
        for metric in metrics:
            metrics_list.append({'expression': 'ga:' + metric})

        for dimension in dimensions:
            dimensions_list.append({'name': 'ga:' + dimension})

        return self.analytics.reports().batchGet(
            body={
                'reportRequests': [
                    {
                        'viewId': VIEW_ID,
                        'dateRanges': [{'startDate': start_date, 'endDate': end_date_formatted}],
                        'metrics': metrics_list,
                        'dimensions': dimensions_list
                    }]
            }
        ).execute()

    @staticmethod
    def generate_table(response):
        # analytics.query(start_date="14", end_date="7", metrics=[
        #     'totalEvents', 'uniqueEvents'
        # ], dimensions=[
        #     'eventAction', 'eventLabel'
        # ])
        column_headers = []
        row_desc = []
        for report in response.get('reports', []):
            column_header = report.get('columnHeader', {})
            rows = report.get('data').get('rows', [])

            for col in column_header:
                if col == 'dimensions':
                    column_headers = [str(val).split(':')[1] for val in column_header[col]]
                if col == 'metricHeader':
                    metrics = column_header[col].get('metricHeaderEntries', [])
                    column_headers.extend([str(val['name']).split(':')[1] for val in metrics])

            for row in rows:
                for key in row:
                    if key == 'dimensions':
                        dimension = row.get('dimensions', [])
                        for dim in dimension:
                            row_desc.append(dim)
                    if key == 'metrics':
                        for met in row.get('metrics', []):
                            for val in met['values']:
                                row_desc.append(val)

        table_headers = []
        for ch in column_headers:
            table_headers.append(GoogleAnalytics.camel_case_join(GoogleAnalytics.camel_case_split(ch)))

        context_rows = GoogleAnalytics.slice_per(row_desc, table_headers.__len__())

        return table_headers, context_rows

    @staticmethod
    def get_metric(response):
        metric_count = 0
        for report in response.get('reports', []):
            rows = report.get('data').get('rows', [])

            for row in rows:
                for key in row:
                    if key == 'metrics':
                        for met in row.get('metrics', []):
                            for val in met['values']:
                                # print(val)
                                metric_count += int(val)

        return metric_count

    @staticmethod
    def get_top_metric(response):
        metric_count = 0
        top_dimension = ''
        for report in response.get('reports', []):
            rows = report.get('data').get('rows', [])

            for row in rows:
                for key in row:
                    if key == 'dimensions':
                        dimension = row.get('dimensions', [])
                        for dim in dimension:
                            metric = row.get('metrics', False)
                            if metric:
                                for met in metric:
                                    vals = met.get('values')
                                    for val in vals:
                                        if int(val) > metric_count:
                                            metric_count = int(val)
                                            top_dimension = dim

        return top_dimension
