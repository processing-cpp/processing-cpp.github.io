;; Variable Scope.
;;
;; Variables have a global or local "scope".
;; For example, variables declared within either the
;; setup() or draw() functions may be only used in these
;; functions. Global variables, variables declared outside
;; of setup() and draw(), may be used anywhere within the program.
;; If a local variable is declared with the same name as a
;; global variable, the program will use the local variable to make
;; its calculations within the current scope. Variables are localized
;; within each block, the space between a { and }.

(import (processing))

(define a 80)  ; Create a global variable "a"

(define (setup)
  (size 640 360)
  (background 0)
  (stroke 255)
  (no-loop))

(define (draw)
  ; Draw a line using the global variable "a"
  (line a 0 a height)

  ; Create a new variable "a" local to the loop
  (let loop ((a 120))
    (when (< a 200)
      (line a 0 a height)
      (loop (+ a 2))))

  ; Create a new variable "a" local to this part of draw()
  (let ((a 300))
    ; Draw a line using the new local variable "a"
    (line a 0 a height))

  ; Make a call to the custom function drawAnotherLine()
  (draw-another-line)

  ; Make a call to the custom function setYetAnotherLine()
  (draw-yet-another-line))

(define (draw-another-line)
  ; Create a new variable "a" local to this method
  (define a 320)
  ; Draw a line using the local variable "a"
  (line a 0 a height))

(define (draw-yet-another-line)
  ; Because no new local variable "a" is set, 
  ; this line draws using the original global
  ; variable "a", which is set to the value 80.
  (line (+ a 2) 0 (+ a 2) height))
