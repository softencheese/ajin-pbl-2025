FROM alpine

LABEL maintainer="ausungju"

# 빌드 도구와 런타임 라이브러리 설치
RUN apk add --no-cache gcc musl-dev make json-c-dev curl-dev readline-dev

# 소스 코드 복사
WORKDIR /build
COPY inc/ inc/
COPY src/ src/
COPY Makefile Makefile
COPY init.sh /usr/bin/init.sh
RUN chmod +x /usr/bin/init.sh

ENTRYPOINT [ "/usr/bin/init.sh" ]