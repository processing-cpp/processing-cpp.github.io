;; Array Objects.
;;
;; Demonstrates the syntax for creating an array of custom objects.

(import (processing))

(define-record-type module (make-module-record x-offset y-offset x y unit x-direction y-direction speed)
  module?
  (x-offset module-x-offset set-module-x-offset!)
  (y-offset module-y-offset set-module-y-offset!)
  (x module-x set-module-x!)
  (y module-y set-module-y!)
  (unit module-unit set-module-unit!)
  (x-direction module-x-direction set-module-x-direction!)
  (y-direction module-y-direction set-module-y-direction!)
  (speed module-speed set-module-speed!))

; Contructor
(define (make-module x-offset-temp y-offset-temp x-temp y-temp speed-temp temp-unit)
  (let ((self (make-module-record 0 0 0.0 0.0 0 0 0 0.0)))
    (set-module-x-direction! self 1)
    (set-module-y-direction! self 1)
    (set-module-x-offset! self x-offset-temp)
    (set-module-y-offset! self y-offset-temp)
    (set-module-x! self x-temp)
    (set-module-y! self y-temp)
    (set-module-speed! self speed-temp)
    (set-module-unit! self temp-unit)
    self))

; Custom method for updating the variables
(define (module-update self)
  (set-module-x! self
                 (+ (module-x self) (* (module-speed self) (module-x-direction self))))
  (when (or (>= (module-x self) (module-unit self)) (<= (module-x self) 0))
    (set-module-x-direction! self (* (module-x-direction self) -1))
    (set-module-x! self (+ (module-x self) (* 1 (module-x-direction self))))
    (set-module-y! self (+ (module-y self) (* 1 (module-y-direction self)))))
  (when (or (>= (module-y self) (module-unit self)) (<= (module-y self) 0))
    (set-module-y-direction! self (* (module-y-direction self) -1))
    (set-module-y! self (+ (module-y self) (* 1 (module-y-direction self))))))

; Custom method for drawing the object
(define (module-display self)
  (fill 255)
  (ellipse (+ (module-x-offset self) (module-x self))
           (+ (module-y-offset self) (module-y self))
           6
           6))

(define unit 40)
(define count 0)
(define mods #f)

(define (setup)
  (size 640 360)
  (no-stroke)
  (define wide-count (quotient width unit))
  (define high-count (quotient height unit))
  (set! count (* wide-count high-count))
  (set! mods (make-vector count #f))

  (define index 0)
  (do ((y 0 (+ y 1))) ((>= y high-count))
    (do ((x 0 (+ x 1))) ((>= x wide-count))
      (vector-set! mods
                   index
                   (make-module (* x unit) (* y unit) (/ unit 2) (/ unit 2) (random 0.05 0.8) unit))
      (set! index (+ index 1)))))

(define (draw)
  (background 0)
  (vector-for-each (lambda (mod) (module-update mod) (module-display mod)) mods))
