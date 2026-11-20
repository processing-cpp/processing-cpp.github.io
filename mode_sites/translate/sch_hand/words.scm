;; Words.
;;
;; The text() function is used for writing words to the screen.
;; The letters can be aligned left, center, or right with the
;; textAlign() function.

(import (processing))

(define f #f)

(define (setup)
  (size 640 360)

  ; Create the font
  (set! f (create-font "SpaceMono-Regular.ttf" 18))
  (text-font f))

(define (draw)
  (background 102)
  (text-align RIGHT)
  (draw-type (* width 0.25))
  (text-align CENTER)
  (draw-type (* width 0.5))
  (text-align LEFT)
  (draw-type (* width 0.75)))

(define (draw-type x)
  (line x 0 x 65)
  (line x 220 x height)
  (fill 0)
  (text "ichi" x 95)
  (fill 51)
  (text "ni" x 130)
  (fill 204)
  (text "san" x 165)
  (fill 255)
  (text "shi" x 210))
