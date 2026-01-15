NAME:= virt_reader
CC:= gcc
IMAGE_NAME:= embedded_virt_reader
CONTAINER_NAME:= virt_reader_container

# make COM_PORT_BASE_NAME=COM01
COM_PORT_BASE_NAME ?= NONE

CFLAGS:= -Wall -Wextra -g -DCOM_PORT_BASE_NAME=\"$(COM_PORT_BASE_NAME)\"

LDFLAGS:= -ljson-c -lcurl -lreadline

SRCS:=	src/main.c \
		src/virt.c	\
		src/readline.c \
		src/API.c \
		src/utils.c \
		src/init.c

.PHONY: all docker-build docker-run docker-clean code-clean code-re docker-tui

all: docker-tui

docker-build:
	@if ! docker images --format "{{.Repository}}" | grep embedded_virt_reader > /dev/null 2>&1; then \
		docker build -t $(IMAGE_NAME) .; \
	fi

docker-run: docker-build
	@if [ "$(COM_PORT_BASE_NAME)" = "NONE" ]; then \
		echo -e "Please specify COM_PORT_BASE_NAME. e.g., \033[1;32mmake COM_PORT_BASE_NAME=COM00\033[0m"; \
		exit 1; \
	fi
	docker run -it --rm --name $(COM_PORT_BASE_NAME) \
		--network host \
		-e COM_PORT_BASE_NAME=$(COM_PORT_BASE_NAME) \
		$(IMAGE_NAME)

docker-tui: docker-build
	@. ./venv/bin/activate && python3 run_containers.py

docker-clean:
	docker rmi -f $(IMAGE_NAME) || true

$(NAME): $(SRCS)
	@ $(CC) $(CFLAGS) $^ -o $@ $(LDFLAGS)

code-clean:
	rm -f $(NAME)

code-re: code-clean $(NAME)
