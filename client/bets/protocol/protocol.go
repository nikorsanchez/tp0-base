package protocol

import (
    "encoding/binary"
    "fmt"
    "io"
    "net"
    "os"

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
        bet.Agency,
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

func WaitForConfirmation(conn net.Conn) error {
    header := make([]byte, HeaderSize)
    if err := readData(conn, header); err != nil {
        return fmt.Errorf("read confirmation header: %w", err)
    }
    
    msgType := header[0]
    length := binary.BigEndian.Uint16(header[1:3])
    
    if msgType == HeaderTypeFailure {
        return fmt.Errorf("received bet has failed to be stored")
    }

    if msgType != HeaderTypeFailure && msgType != HeaderTypeConfirm {
        return fmt.Errorf("unexpected message type: %d, expected confirmation", msgType)
    }
    
    if length != 0 {
        body := make([]byte, length)
        if err := readData(conn, body); err != nil {
            return fmt.Errorf("read confirmation body: %w", err)
        }
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