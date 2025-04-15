
import requests
from dotenv import load_dotenv
from proxies.proxy_manager import get_proxies
import random
from db.core import IsDbCreated
from db.core import Db
import json
from threading import Thread
import time


load_dotenv(override=True)

def func_chunk_array(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def get_rows_in_batches(model, batch_size=1000):
    offset = 0
    while True:
        sql = f'SELECT * FROM {model.table_tasks} WHERE status=1 LIMIT {batch_size} OFFSET {offset}'
        batch = model.select(sql)
        if not batch:
            break
        yield batch
        offset += batch_size

class TreadGеtProducts():
    def run(self, threads_count: int = 10) -> None:
        # self.proxies = get_proxies()
        # model = Db()
        # sql = f'SELECT * FROM {model.table_tasks} WHERE status=1 LIMIT '
        # rows = model.select(sql)
        # countThread = round(len(rows) / int(threads_count)) + 1
        # threads = [Thread(target=self.run_tread, args=(chunk,)) for chunk in func_chunk_array(rows, countThread)]
        # for thread in threads:
        #     thread.start()

        self.proxies = get_proxies()
        model = Db()
        batch_size = 1000
        for batch in get_rows_in_batches(model, batch_size):
            countThread = round(len(batch) / int(threads_count)) + 1
            threads = [Thread(target=self.run_tread, args=(chunk,)) for chunk in func_chunk_array(batch, countThread)]
            for thread in threads:
                thread.start()
                time.sleep(0.1)  # невелика затримка, щоб не навантажити CPU
            for thread in threads:
                thread.join()

    def run_tread(self, rows: list) -> None:
        GеtProducts(self.proxies).run(rows)


class GеtProducts():
    def __init__(self, list_proxies:list):
        self.list_proxies = list_proxies 
        self.model = Db()

    def run(self, resp_data_list):
        for resp_data in resp_data_list:
            id = resp_data[0]
            result = {}
            result['year'] = resp_data[1]
            result['make'] = resp_data[2]
            result['model'] = resp_data[3]
            result['engine'] = resp_data[4]
            datas = json.loads(resp_data[5])

            datas = datas.get('result',{}).get('columns',{}).get('PartNumber',{}).get('results')
            error = 1
            for data in datas:
                try:
                    cat = data.get('props',{}).get('ProductCategory')
                    if cat and cat == 'Belt Drive System':
                        part = data.get('props',{}).get('ProductNr')
                        if not part:
                            continue
                        result['Part_number'] = part
                        result['Application'] = data.get('props',{}).get('ApplicationDescription')
                        result['Product_Type'] = data.get('props',{}).get('ProductType')
                        url = 'https://navigates.gates.com/us' + data.get('href')
                        params = {
                            'ProductNr': part,
                            'BrandName': 'gates',
                            'SearchType': 'vehicle',
                            'Reset': '1',
                        }
                        response = self.get_response(params)
                        resultsSpec = response.get('result',{}).get('prod',{}).get('Specs')
                        if not resultsSpec:
                            print('No resultsSpec. ', params)
                            error += 1
                            self.update_status(id, 4)
                            continue
                        specs = {}
                        for spec in resultsSpec:
                            specs[spec['Criteria']]=spec['Value']

                        result.update({'Specs':specs})
                        self.insert_datas(result, url)
                except Exception as ex:
                    print('ERROR: ',ex)
                    error += 1
                    self.update_status(id, 3)
                    continue
            if error == 1:
                self.update_status(id, 2)

    def update_status(self, id: int, status: int):
        sql = f"UPDATE {self.model.table_tasks} SET status=%s WHERE id=%s"
        self.model.insert(sql,(status,id))

   
    def insert_datas(self, res: dict, url: str):
        sql = f"INSERT INTO {self.model.table_datas} (datas, URL) VALUES (%s,%s)"
        print(res)
        self.model.insert(sql, (json.dumps(res), url))
        

    def get_link_response(self, link: str, count_try: int = 0) -> str:
        proxy = random.choice(self.list_proxies)
        proxies = {
            'http': proxy,
            'https': proxy
        }
        try:
            response = requests.get(link, 
                                    headers=self.get_headers(),
                                    proxies=proxies)

            return response.text
        except Exception as ex:
            print(ex)
        if count_try > 5:
            raise Exception('no data')
        return self.get_response(link, count_try+1)


    def get_response(self, params: dict, count_try: int = 0) -> dict:
        proxy = random.choice(self.list_proxies)
        proxies = {
            'http': proxy,
            'https': proxy
        }
        try:
            response = requests.get(
                'https://api-v3-us.partsb2.com/api/Gates-US/Product/GetProductUSDetails',
                params=params,
                headers=self.get_headers(),
                proxies=proxies
            )
            response.raise_for_status()
            return response.json()
        except Exception as ex:
            print(ex)
        if count_try > 5:
            raise Exception('no data')
        return self.get_response(params, count_try+1)

    def get_headers(self) -> dict:
        headers = {
            'abp-tenantid': '36',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,uk;q=0.6',
            'b2v4apikey': 'gatesus.92mcsQV5ietS8VlTnpRuA1mWbJ0EjGdL/gmeqD91g9o=',
            'gates_country': 'USA',
            'gates_object_id': 'E1079129285',
            'gates_server_id': '3',
            'origin': 'https://navigates.gates.com',
            'priority': 'u=1, i',
            'referer': 'https://navigates.gates.com/',
            'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }
        return headers



if __name__ == "__main__":
    # IsDbCreated().check()
    TreadGеtProducts().run()