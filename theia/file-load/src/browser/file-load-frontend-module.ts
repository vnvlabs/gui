/**
 * Generated using theia-extension-generator
 */
import { ContainerModule } from '@theia/core/shared/inversify';
import { FileLoadContribution, BreadcrumbsFilterService, CustomApplicationShell } from './file-load-contribution';
import { FrontendApplicationContribution} from '@theia/core/lib/browser';
import { ApplicationShell } from '@theia/core/lib/browser';

import { BreadcrumbsService } from '@theia/core/lib/browser';

export default new ContainerModule( (bind, unbind, isBound, rebind)=> {

    // Replace this line with the desired binding, e.g. "bind(CommandContribution).to(FileLoadContribution)
    bind(FrontendApplicationContribution).toService(FileLoadContribution);
    bind(FileLoadContribution).toSelf();
    
    bind(CustomApplicationShell).toSelf().inSingletonScope();
    rebind(ApplicationShell).to(CustomApplicationShell).inSingletonScope();

     bind(BreadcrumbsFilterService).toSelf().inSingletonScope();
    rebind(BreadcrumbsService).to(BreadcrumbsFilterService);
});

