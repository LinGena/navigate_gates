import requests
from dotenv import load_dotenv
from proxies.proxy_manager import get_proxies
import random
from db.core import IsDbCreated
from db.core import Db
import json
import time
from utils.func import func_chunk_array
from threading import Thread
from utils.func import write_to_file_json


load_dotenv(override=True)

class GetTreadPagesContent():
    def run(self, threads_count: int = 10) -> None:
        years = list(range(1980, 2026))
        chunks = func_chunk_array(years, threads_count)
        for i, chunk in enumerate(chunks):
            print(f"Thread {i+1}: {chunk}")
            thread = Thread(target=self.run_tread, args=(chunk,))
            thread.start()

    def run_tread(self, years: list) -> None:
        GenerateTask().run(years)



class GenerateTask():
    def __init__(self):
        self.list_proxies = get_proxies()
        self.model = Db()

    def run(self, years: list):
        for year in years:
            try:
                self.b2v4apikey = None
                while not self.b2v4apikey:
                    try:
                        self.b2v4apikey = self.get_api_key()
                    except Exception as ex:
                        print(ex)
                result = {}
                result['year'] = year
                result['status'] = 1
                data = {
                    "EquipmentClass":"Passenger Cars & Light Trucks",
                    "EquipmentYear":str(year),
                    "q":"",
                    "CompressedSearch":False
                    }
                resp_makes = self.get_response(data)
                makes = resp_makes.get('result',{}).get('columns',{}).get('EquipmentMake',{}).get('results')
                # if not makes:
                #     result['status'] = 2
                #     result['make'] = None
                #     result['model'] = None
                #     result['engine'] = None
                #     result['response'] = json.dumps(resp_makes)
                #     self.insert_datas(result)
                #     result['status'] = 1
                #     continue
                for make in makes:
                    try:
                        data.update({"EquipmentMake":make['key']})
                        result['make'] = make['text']
                        resp_models = self.get_response(data)
                        models = resp_models.get('result',{}).get('columns',{}).get('EquipmentModel',{}).get('results')
                        # if not models:
                        #     models = resp_makes.get('result',{}).get('columns',{}).get('EquipmentModel',{}).get('results')
                        #     if not models:
                        #         result['status'] = 2
                        #         result['model'] = None
                        #         result['engine'] = None
                        #         result['response'] = json.dumps(resp_models)
                        #         self.insert_datas(result)
                        #         result['status'] = 1
                        #         continue
                        for model in models:
                            try:
                                data.update({"EquipmentModel":model['key']})
                                result['model'] = model['text']
                                resp_engines = self.get_response(data)
                                engines = resp_engines.get('result',{}).get('columns',{}).get('EquipmentEngine',{}).get('results')
                                # if not engines:
                                #     engines = resp_models.get('result',{}).get('columns',{}).get('EquipmentEngine',{}).get('results')
                                #     if not engines:
                                #         engines = resp_makes.get('result',{}).get('columns',{}).get('EquipmentEngine',{}).get('results')
                                #         if not engines:
                                #             result['status'] = 2
                                #             result['engine'] = None
                                #             result['response'] = json.dumps(resp_engines)
                                #             self.insert_datas(result)
                                #             result['status'] = 1
                                #             continue
                                for engine in engines:
                                    try:
                                        data.update({"EquipmentEngine":engine['key']})
                                        result['engine'] = engine['text']

                                        res_data = {
                                            "EquipmentClass":data['EquipmentClass'],
                                            "EquipmentYear":data['EquipmentYear'],
                                            "EquipmentMake":data['EquipmentMake'],
                                            "EquipmentModel":data['EquipmentModel'],
                                            "EquipmentEngine":data['EquipmentEngine'],
                                            "source":"result",
                                            "search_type":None,
                                            "page":0
                                        }
                                        resp_data = self.get_response(res_data)
                                        try:
                                            result['response'] = json.dumps(resp_data)
                                        except:
                                            result['response'] = None
                                        self.insert_datas(result)  
                                    except Exception as ex:
                                        print(ex) 
                            except Exception as ex:
                                print(ex)
                    except Exception as ex:
                        print(ex)
            except Exception as ex:
                print(ex)

    def get_api_key(self):
        headers = {
            '0': '[object Object]',
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9,en;q=0.9;q=0.8',
            'content-type': 'application/json',
            'dnt': '1',
            'priority': 'u=1, i',
            'referer': 'https://navigates.gates.com/',
            'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        }
        params = {
            'd': str(int(time.time() * 1000)),
        }
        proxy = random.choice(self.list_proxies)
        proxies = {
            'http': proxy,
            'https': proxy
        }
        response = requests.get(
            'https://navigates.gates.com/us/assets/config/appconfig.production.json',
            params=params,
            proxies=proxies,
            headers=headers,
        )
        data = response.json()
        return data['remoteServiceApiKey']


    def insert_datas(self, result: dict):
        try:
            print(result.get('year'), result.get('make'), result.get('model'), result.get('engine'))
            value_placeholders = ', '.join(['%s'] * len(result)) 
            sql = f"INSERT INTO {self.model.table_tasks} ({', '.join(result.keys())}) VALUES ({value_placeholders})"
            self.model.insert(sql, list(result.values()))
        except Exception as ex:
            print(ex)

    def get_response(self, data: dict, count_try: int = 0) -> dict:
        headers = {
            'abp-tenantid': '36',
            'accept': 'text/plain',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,uk;q=0.6',
            'b2v4apikey': str(self.b2v4apikey),
            'cache-control': 'no-cache',
            'content-type': 'application/json-patch+json',
            'expires': 'Sat, 01 Jan 2000 00:00:00 GMT',
            'gates_country': 'USA',
            'gates_object_id': 'E1079129285',
            'gates_server_id': '3',
            'origin': 'https://navigates.gates.com',
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'referer': 'https://navigates.gates.com/',
            'sec-ch-ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
        }
        proxy = random.choice(self.list_proxies)
        proxies = {
            'http': proxy,
            'https': proxy
        }
        try:
            response = requests.post('https://api-v3-us.partsb2.com/api/Gates-US/Search/AutoSearchUS', 
                                    headers=headers, 
                                    data=json.dumps(data),
                                    proxies=proxies, 
                                    timeout=20)
            response.raise_for_status()
            return response.json()
        except Exception as ex:
            # print(ex)
            pass
        if count_try > 20:
            print('no data')
            return None
        return self.get_response(data, count_try+1)


        

if __name__ == "__main__":
    IsDbCreated().check()
    GetTreadPagesContent().run()




