;; The Mandelbrot Set
;; by Daniel Shiffman.
;; (slight modification by l8l)
;;
;; Simple rendering of the Mandelbrot set.

(import (processing))

(define (setup)
  (size 640 360)
  (no-loop)
  (background 255)

  ; Establish a range of values on the complex plane
  ; A different range will allow us to "zoom" in or out on the fractal

  ; It all starts with the width, try higher or lower values
  (define w 4)
  (define h (/ (* w height) width))

  ; Start at negative half the width and height
  (define xmin (/ (- w) 2))
  (define ymin (/ (- h) 2))

  ; Make sure we can write to the pixels[] array.
  ; Only need to do this once since we don't do any other drawing.
  (load-pixels)

  ; Maximum number of iterations for each point on the complex plane
  (define maxiterations 100)

  ; x goes from xmin to xmax
  (define xmax (+ xmin w))
  ; y goes from ymin to ymax
  (define ymax (+ ymin h))

  ; Calculate amount we increment x,y for each pixel
  (define dx (/ (- xmax xmin) width))
  (define dy (/ (- ymax ymin) height))

  ; Start y
  (define y ymin)
  (do ((j 0 (+ j 1))) ((>= j height))
    ; Start x
    (define x xmin)
    (do ((i 0 (+ i 1))) ((>= i width))
      ; Now we test, as we iterate z = z^2 + c does z tend towards infinity?
      (define a x)
      (define b y)
      (define n 0)
      (define max-v 4.0)  ; Infinity in our finite world is simple, let's just consider it 4
      (define abs-old 0.0)
      (define converge-number maxiterations)  ; this will change if the while loop breaks due to non-convergence
      (define escaped #f)
      (do () ((or escaped (>= n maxiterations)))
        ; We suppose z = a+ib
        (define aa (* a a))
        (define bb (* b b))
        (define abs-v (sqrt (+ aa bb)))  ; |z| = sqrt(a^2+b^2)
        (cond
          ((> abs-v max-v)
           ; Now measure how much we exceeded the maximum:
           (define diff-to-last (- abs-v abs-old))
           (define diff-to-max (- max-v abs-old))
           (set! converge-number (+ n (/ diff-to-max diff-to-last)))
           (set! escaped #t))  ; Bail
          (else
           (define twoab (* 2.0 a b))
           (set! a (+ (- aa bb) x))  ; this operation corresponds to z -> z^2+c where z=a+ib c=(x,y)
           (set! b (+ twoab y))
           (set! n (+ n 1))
           (set! abs-old abs-v))))

      ; We color each pixel based on how long it takes to get to infinity
      ; If we never got there, let's pick the color black
      (cond
        ((= n maxiterations) (vector-set! pixels (+ i (* j width)) (color 0)))
        (else
          ; Gosh, we could make fancy colors here if we wanted
          (define norm-v (map converge-number 0 maxiterations 0 1))
          (vector-set! pixels (+ i (* j width)) (color (map (sqrt norm-v) 0 1 0 255)))))
      (set! x (+ x dx)))
    (set! y (+ y dy)))
  (update-pixels))
