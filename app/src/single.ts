import { autoinject } from 'aurelia-framework';
import { App } from './app';
import { Luncho,  } from 'luncho_typescript-aurelia/luncho';
import { ILunchoDataParams } from 'luncho_typescript-aurelia/LunchoApi';
import { LunchoData } from 'luncho_typescript-aurelia/models';
// import { LunchoApi } from 'luncho_typescript-aurelia/LunchoApi';
//import { LunchoApi, LunchoData } from 'luncho_typescript-aurelia';
//import { LunchoApi, LunchoData } from './gen-openapi';

@autoinject
export class Single {
    app: App;
    luncho: Luncho;
    countryCode: string = 'JP';
    lunchoValue: number = 100;
    lunchoData: LunchoData;
    local_currency_value: number;
    dollar_value: number;

    constructor(app: App, luncho: Luncho) {
        this.luncho = luncho;
        this.app = app;
    }

    async activate() {
        // download country codes and names
        await this.luncho.getCountries();
    }

    attached() {
        this.convertFromLuncho();
    }

    async convertFromLuncho() {
        this.lunchoData = await this.luncho.lunchoData({countryCode: this.countryCode});
        this.local_currency_value = await this.luncho.localCurrencyFromLuncho(this.lunchoValue, this.countryCode);
        this.dollar_value = await this.luncho.USDollarFromLuncho(this.lunchoValue, this.countryCode);

        // this.luncho.localCurrencyFromLuncho({countryCode: this.countryCode, lunchoValue: Number(this.lunchoValue)})
        //     .then((result: LunchoData) => {
        //         this.result = result;
        //     });
    }
}
