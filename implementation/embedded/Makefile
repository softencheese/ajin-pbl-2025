NAME:= nfc_reader
# CC:= aarch64-linux-gnu-gcc -gnu
CC:= gcc
CFLAGS:= -Wall -Wextra -Werror -g

RFID_LIB_DIR:= -L./lib
RFID_LIB:= -lcomPro
JSON_LIB_DIR:= -I./json-c-build
JSON_LIB:= -ljson-c
LDFLAGS:= $(RFID_LIB_DIR) $(RFID_LIB) $(JSON_LIB_DIR) $(JSON_LIB) -lcurl -Wl,-rpath,./lib

INCLUDE_DIR:= -I./inc/nfc  \
	         -I./inc/json

SRCS:=	src/main.c \
		src/rfid.c	\
		src/barcode.c \
		src/API.c \
		src/utils.c \
		src/init.c

all: $(NAME)

$(NAME): $(SRCS)
	@ $(CC) $(CFLAGS) $(INCLUDE_DIR) $^ -o $@ $(LDFLAGS)

clean:
	rm -f $(NAME)

re: clean all