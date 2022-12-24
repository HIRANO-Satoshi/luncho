# patch generated runtime.ts and yarn install and make a symlink
#
#

cd ../luncho-typescript-fetch
# export type FetchAPI = GlobalFetch['fetch'];
#  ->
#    export type FetchAPI = typeof fetch;
if [ ! -e src/runtime.ts.org ]; then
    mv src/runtime.ts src/runtime.ts.org
fi
sed -e "s/GlobalFetch\['fetch'\]/typeof fetch/" src/runtime.ts.org >src/runtime.ts


# add "export * from './luncho';" to src/index.ts
if [ ! -e src/index.ts.org ]; then
    cp src/index.ts src/index.ts.org
fi
if [ "`grep luncho src/index.ts`" == "" ]; then
    echo "export * from './luncho';" >>src/index.ts
fi

yarn install
yarn link


cd ../app/src
yarn link "luncho-typescript-fetch"
#ln -sf ../../luncho-typescript-fetch/src luncho-typescript-fetch
cd ..
yarn install

cd ../server
