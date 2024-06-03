let channelUuid = crypto.randomUUID();
fetch(`http://localhost:8000/events/${channelUuid}/`)
    .then((data) => {
        console.log(`Channel ${channelUuid} open`)
        console.log(data.status)
    })
    .catch((error) => console.log('Error ' + error.status));

// start sending messages
fetch(`http://localhost:8000/events/${channelUuid}/send`).then();
