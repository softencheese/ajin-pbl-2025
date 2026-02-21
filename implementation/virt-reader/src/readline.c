#include "../inc/main.h"

extern t_scannerInfo *g_in_nfc_data;
extern t_scannerInfo *g_out_nfc_data;
extern t_scannerInfo *g_reg_nfc_data;


static int process_input_line(char *line, t_data *data)
{
	char prefix;
	t_scannerInfo *scanner;

	if (line == NULL || strcmp(line, "quit") == 0 || strcmp(line, "exit") == 0)
	{
		data->program_running = 0;
		printf("\n");
		return -1;
	}
    line[0] = toupper(line[0]);
	if (strlen(line) == 0)
		return 0;

	add_history(line);

	prefix = line[0];
	if (prefix == 'I')
		scanner = g_in_nfc_data;
	else if (prefix == 'O')
		scanner = g_out_nfc_data;
	else if (prefix == 'R')
		scanner = g_reg_nfc_data;
    else if (prefix == 'L')
	{
        manager_process_lots_command(data, line);
		return 0;
	}
	else
	{
		printf("Invalid command. Use [I] or [O], [R] prefix (e.g., I 1A2B3C4D)\n");
		return 0;
	}

	if (strlen(line) < 3)
	{
		printf("Invalid input format. Expected: <I|O|R> <CARD_ID>\n");
		return 0;
	}

	process_card_input(line + 2, NULL, scanner);

	return 0;
}

void run_input_loop(t_data *data)
{
	using_history();

	while (data->program_running)
	{
		char *line = readline("> ");
		int res = process_input_line(line, data);
		
		if (line != NULL)
			free(line);
		
		if (res == -1)
		{
			if (g_in_nfc_data != NULL)
			{
				printf("Sending OFFLINE status for: %s\n", g_in_nfc_data->port_name);
				json_object *json = set_API_sendData_readerStatus(g_in_nfc_data, "OFFLINE");
				Post_JSON_to_API(json, API_URL_READER_STATUS, true);
			}
			
			if (g_out_nfc_data != NULL)
			{
				printf("Sending OFFLINE status for: %s\n", g_out_nfc_data->port_name);
				json_object *json = set_API_sendData_readerStatus(g_out_nfc_data, "OFFLINE");
				Post_JSON_to_API(json, API_URL_READER_STATUS, true);
			}

			if (g_reg_nfc_data != NULL)
			{
				printf("Sending OFFLINE status for: %s\n", g_reg_nfc_data->port_name);
				json_object *json = set_API_sendData_readerStatus(g_reg_nfc_data, "OFFLINE");
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
	printf("  [I] <CARD_ID> - Send to IN port (" COM_PORT_BASE_NAME "_IN)\n");
	printf("  [O] <CARD_ID> - Send to OUT port (" COM_PORT_BASE_NAME "_OUT)\n");
	printf("  [R] <CARD_ID> - Send to Register port (" COM_PORT_BASE_NAME "_REG)\n");
    printf("  [L] <command> - Manager lots command (e.g., L list)\n");
	printf("  quit/exit    - Exit program\n");
	printf("\nExample: I 1A2B3C4D or O 04 3F 28 AA\n\n");
}
