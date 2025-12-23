#include "../inc/main.h"

t_scannerInfo *g_reg_nfc_data = NULL;
t_scannerInfo *g_gen_nfc_data = NULL;

void signal_handler(int sig)
{
	(void)sig;

	printf("\n=== Shutting down ===\n");
	
	if (g_reg_nfc_data != NULL)
	{
		printf("Sending OFFLINE status for: %s\n", g_reg_nfc_data->port_name);
		json_object *json = set_API_sendData_readerStatus(g_reg_nfc_data, "OFFLINE");
		printf("%s\n", json_object_to_json_string(json));
		Post_JSON_to_API(json, API_URL_READER_STATUS, true);
	}
	
	if (g_gen_nfc_data != NULL)
	{
		printf("Sending OFFLINE status for: %s\n", g_gen_nfc_data->port_name);
		json_object *json = set_API_sendData_readerStatus(g_gen_nfc_data, "OFFLINE");
		Post_JSON_to_API(json, API_URL_READER_STATUS, true);
	}
	
	exit(0);
}

int main()
{
	t_data data;
	t_scannerInfo reg_nfc_data;
	t_scannerInfo gen_nfc_data;
	t_statusThreadData status_thread_data;

	setup(&data, &reg_nfc_data, &gen_nfc_data, &status_thread_data);

	printf("Auto detect cards\n\n");
	pthread_t gen_nfc_thread, reg_nfc_thread, status_thread;
	if (pthread_create(&reg_nfc_thread, NULL, (void *)detectCards, (void *)&reg_nfc_data) != 0 || 
		pthread_create(&gen_nfc_thread, NULL, (void *)detectCards, (void *)&gen_nfc_data) != 0 ||
		pthread_create(&status_thread, NULL, (void *)run_status_thread, (void *)&status_thread_data) != 0)
	{
		printf("Failed to create NFC scanning thread\n");
		return -1;
	}
	
	pthread_join(reg_nfc_thread, NULL);
	pthread_join(gen_nfc_thread, NULL);

	return 0;
}
