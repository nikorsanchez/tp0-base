package protocol

import (
    "encoding/binary"
    "fmt"
    "io"
    "net"
    "os"
    "strings"

    "github.com/7574-sistemas-distribuidos/docker-compose-init/client/bets/models"
)

func SendBet(conn net.Conn, bet *models.Bet) error {
    message := buildBetMessage(bet)
    
    if len(message) > MaxMessageSize {
        return fmt.Errorf("bet too large: %d bytes", len(message))
    }

    header := make([]byte, HeaderSize)
    header[0] = HeaderTypeBet
    binary.BigEndian.PutUint16(header[1:3], uint16(len(message)))

    if err := writeFull(conn, header); err != nil {
        return fmt.Errorf("send header: %w", err)
    }
    
    if err := writeFull(conn, message); err != nil {
        return fmt.Errorf("send body: %w", err)
    }
    
    return nil
}

func buildBetMessage(bet *models.Bet) []byte {
    fields := []string{
        bet.FirstName,
        bet.LastName,
        bet.Document,
        bet.Birthdate,
        bet.Number,
    }
    
    var message []byte
    for i, field := range fields {
        if i > 0 {
            message = append(message, FieldSeparator)
        }
        message = append(message, []byte(field)...)
    }
    message = append(message, FieldEndMarker)
    
    return message
}

func parseBetMessage(data []byte) (*models.Bet, error) {
    if len(data) > 0 && data[len(data)-1] == FieldEndMarker {
        data = data[:len(data)-1]
    }
    
    parts := strings.Split(string(data), string(FieldSeparator))
    if len(parts) != 5 {
        return nil, fmt.Errorf("invalid message format: expected 5 fields, got %d", len(parts))
    }
    
    return &models.Bet{
        FirstName: parts[0],
        LastName:  parts[1],
        Document:  parts[2],
        Birthdate: parts[3],
        Number:    parts[4],
    }, nil
}

func WaitForConfirmation(conn net.Conn) error {
    header := make([]byte, HeaderSize)
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

// Reads all bytes from the connection preventing short reads
func readData(r io.Reader, buf []byte) error {
    _, err := io.ReadFull(r, buf)
    return err
}

// Writes all bytes to the connection preventing short writes
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