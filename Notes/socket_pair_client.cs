﻿using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading;

using ZeroMQ;

namespace Examples
{
    static partial class Program
    {
        public static void PSEnvSub(string[] args)
        {
            //
            // Pubsub envelope subscriber
            //
            // Author: metadings
            //

            // Prepare our context and subscriber
            using (var context = new ZContext())
            using (var subscriber = new ZSocket(context, ZSocketType.SUB))
            {
                subscriber.Connect("tcp://192.168.1.40:5563");
                subscriber.Subscribe("10001");

                int subscribed = 0;
                while (true)
                {
                    using (ZMessage message = subscriber.ReceiveMessage())
                    {
                        subscribed++;

                        // Read envelope with address
                        string address = message[0].ReadString();

                        // Read message contents
                        string contents = message[1].ReadString();

                        Console.WriteLine("{0}. [{1}] {2}", subscribed, address, contents);
                    }
                }
            }
        }
    }
}