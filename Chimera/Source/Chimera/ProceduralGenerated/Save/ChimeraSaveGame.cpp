#include "ChimeraSaveGame.h"
#pragma warning(disable: 4996)
#pragma warning(disable: 5038)

UChimeraSaveGame::UChimeraSaveGame()
{
	SaveVersion = TEXT("1.0.0");
	LastSavedTime = FDateTime::Now();
}
