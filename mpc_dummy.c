#include <stdio.h>

// This is Dummy mpc program for debug.
// echo back args.

int main(int argc, char* argv[])
{
	int i;
	for (i = 0; i < argc; i++)
	{
		printf("%s ", argv[i]);
	}
	return 0;
}