org  0x100               ; Вказуємо, що це програма .COM

section .data
    a db 5               ; Визначаємо a = 5
    b db 3               ; Визначаємо b = 3
    c db 2               ; Визначаємо c = 2
    resultMsg db 'Result: $' ; Рядок з $ для функції 09h

section .text
_start:
    mov al, [b]          ; Завантажуємо b в al
    sub al, [c]          ; Віднімаємо c від al
    add al, [a]          ; Додаємо a в al

    ; Зберігаємо результат у тимчасову змінну
    mov bl, al

    ; Виведення тексту
    mov ah, 09h          ; Функція DOS для виведення рядка
    lea dx, resultMsg    ; Адреса рядка
    int 21h              ; Вивід "Result: "

    ; Перетворення числа в ASCII
    mov al, bl
    add al, 30h

    ; Виведення символу
    mov dl, al
    mov ah, 02h          ; Вивід символу з dl
    int 21h

    ; Завершення програми
    mov ax, 4c00h
    int 21h
