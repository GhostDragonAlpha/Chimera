#include "ChimeraSaveGame.h"

UChimeraSaveGame::UChimeraSaveGame()
{
	SaveVersion = TEXT("1.0.0");
	LastSavedTime = FDateTime::Now();
}
