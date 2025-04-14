import random
import re

CENT_OS_QUERY_INDICES = {
    "logs-apache.access-default", "logs-apache.error-default",
    "logs-mysql.slowlog-default", "logs-nginx.access-default",
    "logs-postgresql.log-default"
}


def extract_index_string(index_name):
    pattern = r"^(.*?)-(\d{4}\.\d{2}\.\d{2})-.*$"
    matched = re.match(pattern, index_name)
    if matched:
        return matched.group(1)
    else:
        return ""


def get_all_indices(es):
    all_indices = es.indices.get_alias(index="*")
    answer = set([extract_index_string(i) for i in dict(all_indices).keys()])
    return answer


def get_random():
    yyyy = 2020
    mm = "0" + str(random.randint(1, 3))
    dd = random.randint(1, 31)

    dd = str(dd) if dd >= 10 else "0" + str(dd)

    return dd, mm, yyyy


def generate_query(index_name):
    dd, mm, yyyy = get_random()

    if (dd == "31" or dd == "30") and mm == "02":
        dd = 25

    query_string = "CentOS Linux" if index_name in CENT_OS_QUERY_INDICES else "error"

    return {
        "query": {
            "bool": {
                "must": [],
                "filter": [
                    {
                        "multi_match": {
                            "type": "best_fields",
                            "query": f"{query_string}",
                            "lenient": True
                        }
                    },
                    {
                        "range": {
                            "@timestamp": {
                                "format": "strict_date_optional_time",
                                "gte": f"{yyyy}-{mm}-{dd}T00:00:01.000Z",
                                "lte": f"{yyyy}-{mm}-{dd}T23:59:59.000Z",
                            }
                        }
                    }
                ],
                "should": [],
                "must_not": []
            }
        },
        "sort": [
            {
                "@timestamp": {
                    "order": "desc"
                }
            }
        ],
        "size": 100
    }


class FrozenQueriesRunner:

    # Will grab the index from params after wards
    # Also, put the iteration in the challenge do not put it here, or we can grab it from params
    # Request time out get it from the params later
    async def __call__(self, es, params):
        all_indices = [i for i in get_all_indices(es) if i]

        query_results = {}

        for index_name in all_indices:
            query = generate_query(index_name=index_name)

            result = await es.search(index=index_name + "*", body=query, request_timeout=120)

            query_results[index_name] = len(result["hits"]["hits"])

        return query_results
