;; Handles.
;;
;; Click and drag the white boxes to change their position.

(import (processing))

(define-record-type handle (make-handle-record x y boxx boxy stretch size over press locked otherslocked others)
  handle?
  (x handle-x set-handle-x!)
  (y handle-y set-handle-y!)
  (boxx handle-boxx set-handle-boxx!)
  (boxy handle-boxy set-handle-boxy!)
  (stretch handle-stretch set-handle-stretch!)
  (size handle-size set-handle-size!)
  (over handle-over set-handle-over!)
  (press handle-press set-handle-press!)
  (locked handle-locked set-handle-locked!)
  (otherslocked handle-otherslocked set-handle-otherslocked!)
  (others handle-others set-handle-others!))

(define (make-handle ix iy il is o)
  (let ((self (make-handle-record 0 0 0 0 0 0 #f #f #f #f #f)))
    (set-handle-locked! self #f)
    (set-handle-otherslocked! self #f)
    (set-handle-x! self ix)
    (set-handle-y! self iy)
    (set-handle-stretch! self il)
    (set-handle-size! self is)
    (set-handle-boxx! self
                      (- (+ (handle-x self) (handle-stretch self))
                         (quotient (handle-size self) 2)))
    (set-handle-boxy! self (- (handle-y self) (quotient (handle-size self) 2)))
    (set-handle-others! self o)
    self))

(define (handle-update self)
  (set-handle-boxx! self (+ (handle-x self) (handle-stretch self)))
  (set-handle-boxy! self (- (handle-y self) (quotient (handle-size self) 2)))

  ; Is any other handle being dragged?
  (set-handle-otherslocked! self #f)
  (let loop ((i 0))
    (when (< i (vector-length (handle-others self)))
      (if (handle-locked (vector-ref (handle-others self) i))
        (set-handle-otherslocked! self #t)
        (loop (+ i 1)))))

  (when (not (handle-otherslocked self))
    (handle-over-event self)
    (handle-press-event self))

  (when (handle-press self)
    (set-handle-stretch! self
                         (lock (- mouse-x (/ width 2) (/ (handle-size self) 2))
                               0
                               (- (/ width 2) (handle-size self) 1)))))

(define (handle-over-event self)
  (if (over-rect (handle-boxx self)
              (handle-boxy self)
              (handle-size self)
              (handle-size self))
    (set-handle-over! self #t)
    (set-handle-over! self #f)))

(define (handle-press-event self)
  (cond
    ((or (and (handle-over self) first-mouse-press) (handle-locked self))
     (set-handle-press! self #t)
     (set-handle-locked! self #t))
    (else (set-handle-press! self #f))))

(define (handle-release-event self) (set-handle-locked! self #f))

(define (handle-display self)
  (line (handle-x self)
        (handle-y self)
        (+ (handle-x self) (handle-stretch self))
        (handle-y self))
  (fill 255)
  (stroke 0)
  (rect (handle-boxx self) (handle-boxy self) (handle-size self) (handle-size self))
  (when (or (handle-over self) (handle-press self))
    (line (handle-boxx self)
          (handle-boxy self)
          (+ (handle-boxx self) (handle-size self))
          (+ (handle-boxy self) (handle-size self)))
    (line (handle-boxx self)
          (+ (handle-boxy self) (handle-size self))
          (+ (handle-boxx self) (handle-size self))
          (handle-boxy self))))

(define handles #f)

; True if a mouse button has just been pressed while no other button was.
(define first-mouse-press #f)

(define (setup)
  (size 640 360)
  (define num (quotient height 15))
  (set! handles (make-vector num #f))
  (define hsize 10)
  (do ((i 0 (+ i 1))) ((>= i (vector-length handles)))
    (vector-set! handles
                 i
                 (make-handle (/ width 2) (+ 10 (* i 15)) (- 50 (/ hsize 2)) 10 handles))))

(define (draw)
  (background 153)

  (do ((i 0 (+ i 1))) ((>= i (vector-length handles)))
    (handle-update (vector-ref handles i))
    (handle-display (vector-ref handles i)))

  (fill 0)
  (rect 0 0 (/ width 2) height)

  ; After it has been used in the sketch, set it back to false
  (when first-mouse-press (set! first-mouse-press #f)))

(define (mouse-pressed) (when (not first-mouse-press) (set! first-mouse-press #t)))

(define (mouse-released)
  (do ((i 0 (+ i 1))) ((>= i (vector-length handles)))
    (handle-release-event (vector-ref handles i))))

(define (over-rect x y width-v height-v)
  (if (and (>= mouse-x x)
        (<= mouse-x (+ x width-v))
        (>= mouse-y y)
        (<= mouse-y (+ y height-v)))
    #t
    #f))

(define (lock val minv maxv) (min (max val minv) maxv))
