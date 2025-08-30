package models

type Bet struct {
    Agency     string `json:"agency"`
    FirstName  string `json:"first_name"`
    LastName   string `json:"last_name"`
    Document   string `json:"document"`
    Birthdate  string `json:"birthdate"`
    Number     string `json:"number"`
}