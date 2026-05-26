FROM golang:1.22-bookworm AS builder

WORKDIR /build

COPY app/go.mod app/go.sum ./
RUN go mod download

COPY app/ ./
RUN CGO_ENABLED=0 go build -o mywebapp .

FROM gcr.io/distroless/static-debian12

COPY --from=builder /build/mywebapp /mywebapp

EXPOSE 5000

CMD ["/mywebapp"]
