package protocol

import (
    "encoding/json"
    "fmt"
    "io"
    "net"
    "os"

    "github.com/7574-sistemas-distribuidos/docker-compose-init/client/bets/models"
)

// bytes
const (
    HeaderTypeBet      = 1
    HeaderTypeConfirm  = 2
    HeaderSize         = 1
    LengthSize         = 3
    FullHeaderSize     = HeaderSize + LengthSize
)

func SendBet(conn net.Conn, bet *models.Bet) error {
    betBytes, err := json.Marshal(bet)
    if err != nil {
        return fmt.Errorf("marshal bet: %w", err)
    }
    if len(betBytes) > 0xFFFFFF {
        return fmt.Errorf("bet too large")
    }

    header := make([]byte, FullHeaderSize)
    header[0] = HeaderTypeBet
    header[1] = byte((len(betBytes) >> 16) & 0xFF)
    header[2] = byte((len(betBytes) >> 8) & 0xFF)
    header[3] = byte(len(betBytes) & 0xFF)

    if err := writeFull(conn, header); err != nil {
        return fmt.Errorf("send header: %w", err)
    }
    if err := writeFull(conn, betBytes); err != nil {
        return fmt.Errorf("send body: %w", err)
    }
    return nil
}

func WaitForConfirmation(conn net.Conn) error {
    header := make([]byte, FullHeaderSize)
    if err := readData(conn, header); err != nil {
        return fmt.Errorf("read confirmation header: %w", err)
    }
    msgType := header[0]
    length := int(header[1])<<16 | int(header[2])<<8 | int(header[3])
    if msgType != HeaderTypeConfirm || length != 0 {
        return fmt.Errorf("unexpected confirmation header: type=%d length=%d", msgType, length)
    }
    return nil
}

func readData(r io.Reader, buf []byte) error {
    _, err := io.ReadFull(r, buf)
    return err
}

func writeFull(conn net.Conn, data []byte) error {
    total := 0
    for total < len(data) {
        n, err := conn.Write(data[total:])
        if err != nil {
            return err
        }
        total += n
    }
    return nil
}

func BetFromEnv() *models.Bet {
    return &models.Bet{
        Agency:    os.Getenv("AGENCIA"),
        FirstName: os.Getenv("NOMBRE"),
        LastName:  os.Getenv("APELLIDO"),
        Document:  os.Getenv("DOCUMENTO"),
        Birthdate: os.Getenv("NACIMIENTO"),
        Number:    os.Getenv("NUMERO"),
    }
}