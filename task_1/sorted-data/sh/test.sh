#!/bin/bash
echo "Hello, world!"
my_name="Irish"
echo $my_name
#calc
a=5
b=10
result=$(($a+$b))
echo "Sum result is $result"
echo "Введіть число"
read num
if [ $num -gt 10 ];
then
echo "Число > 10"
elif [ $num -eq 10 ];
then
echo "Число = 10"
elif [ $num -lt 10 ];
then
echo "Число < 10"
else
echo "Некоректне число"
fi
array_m=(4 1 5)
$(echo "${array_m[@]}" | sort)
