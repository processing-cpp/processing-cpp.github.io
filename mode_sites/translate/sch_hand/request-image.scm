;; Request Image
;; by Ira Greenberg
;;
;; Shows how to use the requestImage() function with preloader animation.
;; The requestImage() function loads images on a separate thread so that
;; the sketch does not freeze while they load. It's useful when you are
;; loading large images. These images are small for a quick download, but
;; try it with your own huge images to get the full effect.

(import (processing))

(define img-count 12)
(define imgs (make-vector img-count #f))
(define img-w 0.0)

; Keeps track of loaded images (true or false)
(define load-states (make-vector img-count #f))

; For loading animation
(define loader-x 0.0)
(define loader-y 0.0)
(define theta 0.0)

(define (setup)
  (size 640 360)
  (set! img-w (/ width img-count))

  ; Load images asynchronously
  (do ((i 0 (+ i 1))) ((>= i img-count))
    (vector-set! imgs i (request-image (string-append "PT_anim" (nf i 4) ".gif")))))

(define (draw)
  (background 0)

  ; Start loading animation
  (run-loader-ani)

  (do ((i 0 (+ i 1))) ((>= i (vector-length imgs)))
    ; Check if individual images are fully loaded
    (when (and (not (= (width (vector-ref imgs i)) 0))
          (not (= (width (vector-ref imgs i)) -1)))
      ; As images are loaded set true in boolean array
      (vector-set! load-states i #t)))
  ; When all images are loaded draw them to the screen
  (when (check-load-states) (draw-images)))

(define (draw-images)
  (define y (quotient (- height (height (vector-ref imgs 0))) 2))
  (do ((i 0 (+ i 1))) ((>= i (vector-length imgs)))
    (image (vector-ref imgs i)
           (* (/ width (vector-length imgs)) i)
           y
           (height (vector-ref imgs i))
           (height (vector-ref imgs i)))))

; Loading animation
(define (run-loader-ani)
  ; Only run when images are loading
  (when (not (check-load-states))
    (ellipse loader-x loader-y 10 10)
    (set! loader-x (+ loader-x 2))
    (set! loader-y (+ (/ height 2) (* (sin theta) (/ height 8))))
    (set! theta (+ theta (/ PI 22)))
    ; Reposition ellipse if it goes off the screen
    (when (> loader-x (+ width 5)) (set! loader-x -5))))

; Return true when all images are loaded - no false values left in array
(define (check-load-states)
  (let loop ((i 0))
    (cond ((= i (vector-length imgs)) #t)
          ((not (vector-ref load-states i)) #f)
          (else (loop (+ i 1))))))
