# Language Technology Project
QA system assignment about music for Language Technology Practical. Completed by Galiya Yeshmagambetova, Malina Chichirau, Tianai Dong, Livia Regus.

To run the program from stdin you can use:

```echo "1  When was Gordon Ramsay born?" | python3 Main.py```

To read the questions from the file, uncomment for loop in Main.py on line 106 and comment the loop for reading from stdin:

``` #for line in f:```

Do not forget to specify the name of your file on line 103:

```f = open("test_questions.txt", "r", encoding="utf-8")```

To exit the program, use Control-D
