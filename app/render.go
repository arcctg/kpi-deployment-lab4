package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

type noteRow struct {
	ID    int
	Title string
}

func renderJSON(w http.ResponseWriter, v any) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(v)
}

func renderNotesListHTML(w http.ResponseWriter, notes []noteRow) {
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	fmt.Fprint(w, `<!DOCTYPE html><html><body><h1>Notes</h1><table border="1"><tr><th>ID</th><th>Title</th></tr>`)
	for _, n := range notes {
		fmt.Fprintf(w, `<tr><td>%d</td><td>%s</td></tr>`, n.ID, n.Title)
	}
	fmt.Fprint(w, `</table></body></html>`)
}

func renderNoteHTML(w http.ResponseWriter, n Note) {
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	fmt.Fprintf(w,
		`<!DOCTYPE html><html><body>`+
			`<h1>Note #%d</h1>`+
			`<p><strong>Title:</strong> %s</p>`+
			`<p><strong>Created:</strong> %s</p>`+
			`<p><strong>Content:</strong><br>%s</p>`+
			`</body></html>`,
		n.ID, n.Title, n.CreatedAt.Format(time.RFC3339), n.Content,
	)
}
