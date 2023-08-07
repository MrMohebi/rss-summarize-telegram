package main

import (
	"github.com/MrMohebi/rss-summarize-telgram.git/common"
	"gopkg.in/ini.v1"
	tele "gopkg.in/telebot.v3"
	"log"
	"time"
)

var isIniInitOnce = false
var IniData *ini.File

// nodemon --exec go run main.go --signal SIGTERM
func main() {
	pref := tele.Settings{
		Token:  IniGet("", "TOKEN"),
		Poller: &tele.LongPoller{Timeout: 60 * time.Second},
	}

	b, err := tele.NewBot(pref)
	if err != nil {
		log.Fatal(err)
		return
	}

	b.Start()
}

func IniSetup() {
	if !isIniInitOnce {
		var err error
		IniData, err = ini.Load("config.ini")
		common.IsErr(err, "Error loading .ini file")
		isIniInitOnce = true
	} else {
		println("initialized inis once")
	}
}

func IniGet(section string, key string) string {
	if IniData == nil {
		IniSetup()
	}
	return IniData.Section(section).Key(key).String()
}
