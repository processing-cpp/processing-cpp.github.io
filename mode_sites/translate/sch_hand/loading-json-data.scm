;; Loading JSON Data
;; by Daniel Shiffman.
;;
;; This example demonstrates how to use loadJSON()
;; to retrieve data from a JSON file and make objects
;; from that data.
;;
;; Here is what the JSON looks like (partial):
;;
;; {
;; "bubbles": [
;; {
;; "position": {
;; "x": 160,
;; "y": 103
;; },
;; "diameter": 43.19838,
;; "label": "Happy"
;; },
;; {
;; "position": {
;; "x": 372,
;; "y": 137
;; },
;; "diameter": 52.42526,
;; "label": "Sad"
;; }
;; ]
;; }
; An Array of Bubble objects

(import (processing))

; A Bubble class

(define-record-type bubble (make-bubble-record x y diameter name over)
  bubble?
  (x bubble-x set-bubble-x!)
  (y bubble-y set-bubble-y!)
  (diameter bubble-diameter set-bubble-diameter!)
  (name bubble-name set-bubble-name!)
  (over bubble-over set-bubble-over!))

; Create  the Bubble
(define (make-bubble x y diameter s)
  (let ((self (make-bubble-record 0.0 0.0 0.0 "" #f)))
    (set-bubble-over! self #f)
    (set-bubble-x! self x)
    (set-bubble-y! self y)
    (set-bubble-diameter! self diameter)
    (set-bubble-name! self s)
    self))

; CHecking if mouse is over the Bubble
(define (bubble-rollover self px py)
  (define d (dist px py (bubble-x self) (bubble-y self)))
  (if (< d (/ (bubble-diameter self) 2))
    (set-bubble-over! self #t)
    (set-bubble-over! self #f)))

; Display the Bubble
(define (bubble-display self)
  (stroke 0)
  (stroke-weight 2)
  (no-fill)
  (ellipse (bubble-x self)
           (bubble-y self)
           (bubble-diameter self)
           (bubble-diameter self))
  (when (bubble-over self)
    (fill 0)
    (text-align CENTER)
    (text (bubble-name self)
          (bubble-x self)
          (+ (bubble-y self) (/ (bubble-diameter self) 2) 20))))

(define bubbles #f)
; A JSON object
(define json #f)

(define (setup) (size 640 360) (load-data))

(define (draw)
  (background 255)
  ; Display all bubbles
  (vector-for-each (lambda (b) (bubble-display b) (bubble-rollover b mouse-x mouse-y))
                   bubbles)
  ;
  (text-align LEFT)
  (fill 0)
  (text "Click to add bubbles." 10 (- height 10)))

(define (load-data)
  ; Load JSON file
  ; Temporary full path until path problem resolved.
  (set! json (load-json-object "data.json"))

  (define bubble-data (get-json-array json "bubbles"))

  ; The size of the array of Bubble objects is determined by the total XML elements named "bubble"
  (set! bubbles (make-vector (length bubble-data) #f))

  (do ((i 0 (+ i 1))) ((>= i (length bubble-data)))
    ; Get each object in the array
    (define bubble (get-json-object bubble-data i))
    ; Get a position object
    (define position (get-json-object bubble "position"))
    ; Get x,y from position
    (define x (get-int position "x"))
    (define y (get-int position "y"))

    ; Get diamter and label
    (define diameter (get-float bubble "diameter"))
    (define label (get-string bubble "label"))

    ; Put object in array
    (vector-set! bubbles i (make-bubble x y diameter label))))

(define (mouse-pressed)
  ; Create a new JSON bubble object
  (define new-bubble (make-hash-table))

  ; Create a new JSON position object
  (define position (make-hash-table))
  (set-int position "x" mouse-x)
  (set-int position "y" mouse-y)

  ; Add position to bubble
  (set-json-object new-bubble "position" position)

  ; Add diamater and label to bubble
  (set-float new-bubble "diameter" (random 40 80))
  (set-string new-bubble "label" "New label")

  ; Append the new JSON bubble object to the array
  (define bubble-data (append (get-json-array json "bubbles") (list new-bubble)))

  ; If the array has more than 10 elements, delete the oldest bubble
  (when (> (length bubble-data) 10) (set! bubble-data (list-tail bubble-data 1)))
  (set-json-array json "bubbles" bubble-data)

  ; Save new data
  (save-json-object json "data/data.json")
  (load-data))
