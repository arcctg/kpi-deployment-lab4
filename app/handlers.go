package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"strings"
	"time"
)

type Note struct {
	ID        int       `json:"id"`
	Title     string    `json:"title"`
	Content   string    `json:"content"`
	CreatedAt time.Time `json:"created_at"`
}

type App struct {
	db *sql.DB
}

func (a *App) handleRoot(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/" {
		http.NotFound(w, r)
		return
	}
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	fmt.Fprint(w, `<!DOCTYPE html><html><body>`+
		`<h1>Notes Service</h1>`+
		`<ul>`+
		`<li>GET /notes — list all notes</li>`+
		`<li>POST /notes — create note (title, content)</li>`+
		`<li>GET /notes/{id} — get note by id</li>`+
		`</ul></body></html>`)
}

func (a *App) handleAlive(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	fmt.Fprint(w, "OK")
}

func (a *App) handleReady(w http.ResponseWriter, r *http.Request) {
	if err := a.db.Ping(); err != nil {
		http.Error(w, "database unavailable: "+err.Error(), http.StatusInternalServerError)
		return
	}
	w.WriteHeader(http.StatusOK)
	fmt.Fprint(w, "OK")
}

func (a *App) handleNotes(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		a.listNotes(w, r)
	case http.MethodPost:
		a.createNote(w, r)
	default:
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
	}
}

func (a *App) handleNoteByID(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	idStr := strings.TrimPrefix(r.URL.Path, "/notes/")
	id, err := strconv.Atoi(idStr)
	if err != nil || id <= 0 {
		http.Error(w, "invalid id", http.StatusBadRequest)
		return
	}

	var n Note
	err = a.db.QueryRow(
		`SELECT id, title, content, created_at FROM notes WHERE id = $1`, id,
	).Scan(&n.ID, &n.Title, &n.Content, &n.CreatedAt)
	if err == sql.ErrNoRows {
		http.NotFound(w, r)
		return
	}
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	accept := r.Header.Get("Accept")
	if strings.Contains(accept, "text/html") {
		renderNoteHTML(w, n)
		return
	}
	renderJSON(w, n)
}

func (a *App) listNotes(w http.ResponseWriter, r *http.Request) {
	rows, err := a.db.Query(`SELECT id, title FROM notes ORDER BY id`)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	var notes []noteRow
	for rows.Next() {
		var n noteRow
		if err := rows.Scan(&n.ID, &n.Title); err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		notes = append(notes, n)
	}
	if notes == nil {
		notes = []noteRow{}
	}

	accept := r.Header.Get("Accept")
	if strings.Contains(accept, "text/html") {
		renderNotesListHTML(w, notes)
		return
	}
	renderJSON(w, notes)
}

func (a *App) createNote(w http.ResponseWriter, r *http.Request) {
	var title, content string

	ct := r.Header.Get("Content-Type")
	if strings.Contains(ct, "application/json") {
		var body struct {
			Title   string `json:"title"`
			Content string `json:"content"`
		}
		if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
			http.Error(w, "invalid json", http.StatusBadRequest)
			return
		}
		title = body.Title
		content = body.Content
	} else {
		if err := r.ParseForm(); err != nil {
			http.Error(w, "invalid form", http.StatusBadRequest)
			return
		}
		title = r.FormValue("title")
		content = r.FormValue("content")
	}

	if title == "" || content == "" {
		http.Error(w, "title and content are required", http.StatusBadRequest)
		return
	}

	var n Note
	err := a.db.QueryRow(
		`INSERT INTO notes (title, content) VALUES ($1, $2) RETURNING id, title, content, created_at`,
		title, content,
	).Scan(&n.ID, &n.Title, &n.Content, &n.CreatedAt)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusCreated)
	accept := r.Header.Get("Accept")
	if strings.Contains(accept, "text/html") {
		renderNoteHTML(w, n)
		return
	}
	renderJSON(w, n)
}
