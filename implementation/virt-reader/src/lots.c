#include "../inc/main.h"

int manager_process_lots_command(t_data *data, const char *line)
{
    char url[256];
    json_object *json = NULL;
    json_object *items = NULL;

    (void)line;

    snprintf(url, sizeof(url), "http://localhost:8000/api/v1/processes/%d/alive-lots", data->process_id);

    if (get_JSON_from_API(url, &json) != 0 || json == NULL) {
        printf("Failed to retrieve lots data from API: %s\n", url);
        return -1;
    }

    items = json_object_object_get(json, "items");
    if (items == NULL || !json_object_is_type(items, json_type_array)) {
        printf("No lots data found for process ID %d\n", data->process_id);
        json_object_put(json);
        return -1;
    }

    printf("Lots for process ID %d:\n", data->process_id);
    for (size_t i = 0; i < json_object_array_length(items); i++) {
        json_object *item = json_object_array_get_idx(items, i);
        
        json_object *lot_number_obj = json_object_object_get(item, "lot_number");
        json_object *item_obj = json_object_object_get(item, "item");
        json_object *status_obj = json_object_object_get(item, "status");
        
        const char *lot_number = lot_number_obj ? json_object_get_string(lot_number_obj) : "N/A";
        const char *item_name = "N/A";
        if (item_obj) {
            json_object *name_obj = json_object_object_get(item_obj, "item_name");
            if (name_obj)
                item_name = json_object_get_string(name_obj);
        }
        const char *status = status_obj ? json_object_get_string(status_obj) : "N/A";
        
        printf("  %zu.  Lot %s - Item: %s - Status: %s\n", i+1, lot_number, item_name, status);
    }
    
    json_object_put(json);
    return 0;
}
    