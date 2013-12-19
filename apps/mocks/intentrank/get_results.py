from mock_tile import mock_tile


# TODO maybe store data about last_result in session
last_result = 1

def get_results(host, result_count):
    global last_result
    results = []

    for i in range (last_result, last_result + result_count):
        results.append(mock_tile(i, host=host))

    last_result += result_count

    return results
