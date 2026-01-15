#include "../inc/main.h"

extern t_scannerInfo *g_reg_nfc_data;
extern t_scannerInfo *g_gen_nfc_data;


static int process_input_line(char *line, t_scannerInfo *reg_nfc, t_scannerInfo *gen_nfc, t_data *data)
{
	char port_id;
	t_scannerInfo *scanner;

	if (line == NULL || strcmp(line, "quit") == 0 || strcmp(line, "exit") == 0)
	{
		data->program_running = 0;
		printf("\n");
		return -1;
	}

	if (strlen(line) == 0)
		return 0;

	add_history(line);

	port_id = toupper(line[0]);
	if (port_id == 'R')
		scanner = reg_nfc;
	else if (port_id == 'G')
		scanner = gen_nfc;
	else
	{
		printf("Invalid command. Use [R] or [G] prefix (e.g., R 1A2B3C4D)\n");
		return 0;
	}

	process_card_input(line + 2, NULL, scanner);

	return 0;
}

void run_input_loop(t_data *data, t_scannerInfo *reg_nfc, t_scannerInfo *gen_nfc)
{
	using_history();

	while (data->program_running)
	{
		char *line = readline("> ");
		int res = process_input_line(line, reg_nfc, gen_nfc, data);
		
		if (line != NULL)
			free(line);
		
		if (res == -1)
		{
			if (g_reg_nfc_data != NULL)
			{
				printf("Sending OFFLINE status for: %s\n", g_reg_nfc_data->port_name);
				json_object *json = set_API_sendData_readerStatus(g_reg_nfc_data, "OFFLINE");
				Post_JSON_to_API(json, API_URL_READER_STATUS, true);
			}
			
			if (g_gen_nfc_data != NULL)
			{
				printf("Sending OFFLINE status for: %s\n", g_gen_nfc_data->port_name);
				json_object *json = set_API_sendData_readerStatus(g_gen_nfc_data, "OFFLINE");
				Post_JSON_to_API(json, API_URL_READER_STATUS, true);
			}

			break;
		}
	}
}

void print_usage(void)
{
	printf("\n=== Terminal Input Mode ===\n");
	printf("Commands:\n");
	printf("  [R] <CARD_ID> - Send to REGISTER port (" COM_PORT_BASE_NAME "_REG)\n");
	printf("  [G] <CARD_ID> - Send to GENERIC port (" COM_PORT_BASE_NAME "_GEN)\n");
	printf("  quit/exit    - Exit program\n");
	printf("\nExample: R 1A2B3C4D or G 04 3F 28 AA\n\n");
}
