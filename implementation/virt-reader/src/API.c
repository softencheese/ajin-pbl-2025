#include "../inc/main.h"

size_t WriteMemoryCallback(void *data, size_t size, size_t nmemb, void *userp) {
    size_t realsize = nmemb * size;
    ResponseData *mem = (ResponseData *)userp;
    
	char *ptr = realloc(mem->data, mem->size + realsize + 1);
    if(!ptr) {
        return 0;
    }
    
    mem->data = ptr;
    memcpy(&(mem->data[mem->size]), data, realsize);
    mem->size += realsize;
    mem->data[mem->size] = 0;
    
    return realsize;
}

int Post_JSON_to_API(json_object *json, const char *url, int is_response_print)
{
	CURL *curl;
	CURLcode res;
	struct curl_slist *headers = NULL;
	ResponseData chunk = {0};


	curl = curl_easy_init();
	if(curl) {
		headers = curl_slist_append(headers, "Content-Type: application/json");
		curl_easy_setopt(curl, CURLOPT_URL, url); 
		curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
		curl_easy_setopt(curl, CURLOPT_POSTFIELDS, json_object_to_json_string(json));
		
		curl_easy_setopt(curl, CURLOPT_CONNECTTIMEOUT, 3L);
		curl_easy_setopt(curl, CURLOPT_TIMEOUT, 5L);

		curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteMemoryCallback);
		curl_easy_setopt(curl, CURLOPT_WRITEDATA, (void *)&chunk);

		res = curl_easy_perform(curl);
		if ( res == CURLE_OK && chunk.data ) {
			if (is_response_print)
				printf("Response from API: %s\n", chunk.data);
    		free(chunk.data);
		} else {
			fprintf(stderr, "curl_easy_perform() failed: %s\n", curl_easy_strerror(res));
		}
		
		curl_slist_free_all(headers);
		curl_easy_cleanup(curl);
		return (res == CURLE_OK) ? 0 : -1;
	} else {
		fprintf(stderr, "Failed to initialize CURL\n");
	}

	json_object_put(json);
	return -1;
}

json_object * set_API_sendData_readerStatus(t_scannerInfo *scanner, const char *status)
{
	json_object *json = json_object_new_object();
	int uptime = get_uptime_seconds(scanner->data);

	json_object_object_add(json, "port_name", json_object_new_string(scanner->port_name));
	json_object_object_add(json, "status", json_object_new_string(status));
	json_object_object_add(json, "last_scan_time", json_object_new_string(scanner->last_scan_time));
	json_object_object_add(json, "uptime_seconds", json_object_new_int(uptime));
	json_object_object_add(json, "total_scans", json_object_new_int(scanner->total_scans));
	json_object_object_add(json, "error_count", json_object_new_int(scanner->error_count));

	return json;
}

json_object * set_API_sendData_scan(const char *epc, t_scannerInfo *scanner)
{
	json_object *json = json_object_new_object();

	json_object_object_add(json, "epc", json_object_new_string(epc));
	json_object_object_add(json, "port_name", json_object_new_string(scanner->port_name));
	json_object_object_add(json, "scan_time", json_object_new_string(scanner->last_scan_time));
	json_object *reader_info = json_object_new_object();
	json_object_object_add(reader_info, "model", json_object_new_string("NFC_Reader"));
	json_object_object_add(reader_info, "antenna", json_object_new_int(1));
	json_object_object_add(reader_info, "rssi", json_object_new_int(0));
	json_object_object_add(json, "reader_info", reader_info);

	return json;
}