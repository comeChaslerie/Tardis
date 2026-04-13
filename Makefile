##
## EPITECH PROJECT, 2025
## Makefile
## File description:
## Makefile
##

SRC =

TEST_SRC =

NAME =	wolf3d

LIB = -L./lib/my_lib -lmy

CC = epiclang

.PHONY: all clean fclean re compile tests_run coverage valgrind

all:
	$(MAKE) -C lib/my_lib all
	$(CC) -o $(NAME) main.c $(SRC) $(LIB)

clean:
	rm -f *.gcno
	rm -f *.gcda
	rm -f unit_tests
	rm -f *.cor
	$(MAKE) -C lib/my_lib clean

fclean:	clean
	rm -f $(NAME)
	$(MAKE) -C lib/my_lib fclean

re:
	$(MAKE) fclean
	$(MAKE) all

compile:
	rm -f $(NAME)
	$(CC) -o $(NAME) main.c $(SRC) $(LIB)
	./$(NAME) ./examples/champions/abel.s

compile_val:
	rm -f $(NAME)
	$(CC) -o $(NAME) main.c $(SRC) $(LIB)
	valgrind ./$(NAME) ./examples/champions/abel.s

valgrind: all
	valgrind --leak-check=full \
         --show-leak-kinds=all \
         --track-origins=yes \
         --log-file=valgrind-out.txt \
         ./$(NAME) ./examples/champions/abel.s

tests_run:	re clean
	epiclang -o unit_tests $(SRC) $(TEST_SRC) -lcriterion --coverage $(LIB)
	./unit_tests

coverage:	tests_run
	gcovr --gcov-executable "llvm-cov-20 gcov" --exclude tests/
	gcovr --branches --gcov-executable "llvm-cov-20 gcov" --exclude tests/


#rules for mac

mac_tests_run:	clean
	gcc -o unit_tests --coverage -lcriterion \
		$(TEST_SRC) $(SRC) $(LIB)

gcovrex:	re
	$(MAKE) mac_tests_run
	./unit_tests
	gcovr --gcov-executable "llvm-cov gcov" \
		--exclude "tests/.*"
	gcovr --txt-metric branch --gcov-executable "llvm-cov gcov" \
		--exclude "tests/.*"

compile_val_mac:
	rm -f $(NAME)
	$(CC) -o $(NAME) $(SRC) $(LIB)
	leaks --atExit -- ./$(NAME)
