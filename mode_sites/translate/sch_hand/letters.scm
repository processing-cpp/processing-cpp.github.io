;; Letters.
;;
;; Draws letters to the screen. This requires loading a font,
;; setting the font, and then drawing the letters.

(import (processing))

(define f #f)

(define (setup)
  (size 640 360)
  (background 0)

  ; Create the font
  (set! f (create-font "SourceCodePro-Regular.ttf" 24))
  (text-font f)
  (text-align CENTER CENTER))

(define (draw)
  (background 0)

  ; Set the left and top margin
  (define margin 10)
  (translate (* margin 4) (* margin 4))

  (define gap 46)
  (define counter 35)

  (do ((y 0 (+ y gap))) ((>= y (- height gap)))
    (do ((x 0 (+ x gap))) ((>= x (- width gap)))
      (define letter (char counter))

      (if (or (eqv? letter #\A)
           (eqv? letter #\E)
           (eqv? letter #\I)
           (eqv? letter #\O)
           (eqv? letter #\U))
        (fill 255 204 0)
        (fill 255))

      ; Draw the letter to the screen
      (text letter x y)

      ; Increment the counter
      (set! counter (+ counter 1)))))
